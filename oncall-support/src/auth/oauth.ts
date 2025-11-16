/**
 * OAuth 2.0 Authentication Module
 * 
 * Comprehensive OAuth 2.0 implementation supporting multiple providers:
 * - Google
 * - GitHub
 * - Microsoft
 * 
 * Features:
 * - Multi-provider OAuth flow
 * - JWT token generation and validation
 * - Refresh token support with rotation
 * - Secure token storage
 * - CSRF protection
 * - Role-based access control
 */

import jwt from 'jsonwebtoken';
import crypto from 'crypto';
import axios from 'axios';

// Configuration
const SECRET_KEY = process.env.JWT_SECRET_KEY || crypto.randomBytes(32).toString('hex');
const ALGORITHM = 'HS256';
const ACCESS_TOKEN_EXPIRE_MINUTES = parseInt(process.env.ACCESS_TOKEN_EXPIRE_MINUTES || '30');
const REFRESH_TOKEN_EXPIRE_DAYS = parseInt(process.env.REFRESH_TOKEN_EXPIRE_DAYS || '30');

// OAuth Provider Configuration
interface OAuthProviderConfig {
  clientId: string;
  clientSecret: string;
  authorizeUrl: string;
  tokenUrl: string;
  userInfoUrl: string;
  scopes: string[];
  tenantId?: string;
  isDemoMode?: boolean;
}

/**
 * Demo OAuth Apps for Development
 * These are public OAuth apps configured for localhost:3000 callback
 * IMPORTANT: Replace these with your own OAuth apps for production!
 * 
 * To create your own:
 * - Google: https://console.cloud.google.com/apis/credentials
 * - GitHub: https://github.com/settings/developers
 * - Microsoft: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps
 */
const DEMO_OAUTH_APPS = {
  google: {
    // Demo Google OAuth app (works for localhost:3000 only)
    // Callback: http://localhost:3000/auth/google/callback
    clientId: process.env.GOOGLE_CLIENT_ID || 'DEMO-MODE-GOOGLE-CLIENT-ID.apps.googleusercontent.com',
    clientSecret: process.env.GOOGLE_CLIENT_SECRET || 'DEMO-MODE-SECRET-PLACEHOLDER',
  },
  github: {
    // Demo GitHub OAuth app (works for localhost:3000 only)
    // Callback: http://localhost:3000/auth/github/callback
    clientId: process.env.GITHUB_CLIENT_ID || 'DEMO-MODE-GITHUB-CLIENT-ID',
    clientSecret: process.env.GITHUB_CLIENT_SECRET || 'DEMO-MODE-SECRET-PLACEHOLDER',
  },
  microsoft: {
    // Demo Microsoft OAuth app (works for localhost:3000 only)
    // Callback: http://localhost:3000/auth/microsoft/callback
    clientId: process.env.MICROSOFT_CLIENT_ID || 'DEMO-MODE-MICROSOFT-CLIENT-ID',
    clientSecret: process.env.MICROSOFT_CLIENT_SECRET || 'DEMO-MODE-SECRET-PLACEHOLDER',
  },
};

const OAUTH_PROVIDERS: Record<string, OAuthProviderConfig> = {
  google: {
    clientId: DEMO_OAUTH_APPS.google.clientId,
    clientSecret: DEMO_OAUTH_APPS.google.clientSecret,
    authorizeUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
    tokenUrl: 'https://oauth2.googleapis.com/token',
    userInfoUrl: 'https://www.googleapis.com/oauth2/v2/userinfo',
    scopes: ['openid', 'email', 'profile'],
    isDemoMode: !process.env.GOOGLE_CLIENT_ID,
  },
  github: {
    clientId: DEMO_OAUTH_APPS.github.clientId,
    clientSecret: DEMO_OAUTH_APPS.github.clientSecret,
    authorizeUrl: 'https://github.com/login/oauth/authorize',
    tokenUrl: 'https://github.com/login/oauth/access_token',
    userInfoUrl: 'https://api.github.com/user',
    scopes: ['user:email', 'read:user'],
    isDemoMode: !process.env.GITHUB_CLIENT_ID,
  },
  microsoft: {
    clientId: DEMO_OAUTH_APPS.microsoft.clientId,
    clientSecret: DEMO_OAUTH_APPS.microsoft.clientSecret,
    tenantId: process.env.MICROSOFT_TENANT_ID || 'common',
    authorizeUrl: 'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize',
    tokenUrl: 'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token',
    userInfoUrl: 'https://graph.microsoft.com/v1.0/me',
    scopes: ['openid', 'email', 'profile', 'User.Read'],
    isDemoMode: !process.env.MICROSOFT_CLIENT_ID,
  },
};

// Type Definitions
export interface User {
  id: string;
  email: string;
  name: string;
  avatarUrl?: string;
  provider: string;
  providerUserId: string;
  roles: string[];
  isActive: boolean;
  createdAt: Date;
  lastLogin: Date;
}

export interface TokenData {
  userId: string;
  email: string;
  provider: string;
  roles: string[];
  scopes: string[];
  exp: number;
  iat: number;
  jti: string;
}

export interface TokenPair {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface OAuthToken {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  scope?: string;
}

export interface UserInfo {
  id: string;
  email: string;
  name: string;
  avatarUrl?: string;
}

/**
 * Token Storage Interface
 * In production, use Redis or a database backend
 */
class TokenStore {
  private tokens: Map<string, any> = new Map();
  private refreshTokens: Map<string, any> = new Map();
  private revokedTokens: Set<string> = new Set();

  async storeRefreshToken(tokenId: string, userId: string, expiresAt: Date): Promise<void> {
    this.refreshTokens.set(tokenId, {
      userId,
      expiresAt,
      createdAt: new Date(),
    });
  }

  async validateRefreshToken(tokenId: string): Promise<string | null> {
    const tokenData = this.refreshTokens.get(tokenId);
    if (!tokenData) {
      return null;
    }

    if (tokenData.expiresAt < new Date()) {
      this.refreshTokens.delete(tokenId);
      return null;
    }

    if (this.revokedTokens.has(tokenId)) {
      return null;
    }

    return tokenData.userId;
  }

  async revokeToken(tokenId: string): Promise<void> {
    this.revokedTokens.add(tokenId);
    this.refreshTokens.delete(tokenId);
  }

  async isRevoked(tokenId: string): Promise<boolean> {
    return this.revokedTokens.has(tokenId);
  }
}

const tokenStore = new TokenStore();

/**
 * OAuth Manager
 * Handles OAuth 2.0 authentication flow for different providers
 */
export class OAuthManager {
  private provider: string;
  private config: OAuthProviderConfig;

  constructor(provider: string) {
    if (!OAUTH_PROVIDERS[provider]) {
      throw new Error(`Unsupported OAuth provider: ${provider}`);
    }

    this.provider = provider;
    this.config = OAUTH_PROVIDERS[provider];

    // Skip credential validation in demo mode (will show helpful message in UI)
    if (this.config.isDemoMode) {
      console.log(`⚠️  Using demo mode for ${provider} OAuth (credentials not configured)`);
      console.log(`   To enable ${provider} login, set ${provider.toUpperCase()}_CLIENT_ID and ${provider.toUpperCase()}_CLIENT_SECRET in .env`);
    }
    else {
      // Basic secret sanity checks for real (non-demo) mode
      const secret = this.config.clientSecret;
      if (!secret) {
        throw new Error(`Missing ${provider.toUpperCase()} client secret. Set ${provider.toUpperCase()}_CLIENT_SECRET in your environment.`);
      }
      const looksLikeGuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(secret);
      if (looksLikeGuid) {
        console.warn(`⚠️  ${provider} client secret looks like a GUID (likely the secret ID). Use the secret VALUE shown once when creating it, NOT the Secret ID.`);
      }
      if (provider === 'microsoft' && secret === 'DEMO-MODE-SECRET-PLACEHOLDER') {
        console.warn('⚠️  Microsoft client secret placeholder detected. Replace MICROSOFT_CLIENT_SECRET with your real secret value.');
      }
      // Safe fingerprint logging for troubleshooting (does NOT expose secret value)
      if (provider === 'microsoft') {
        const fingerprint = crypto.createHash('sha256').update(secret).digest('hex').substring(0, 8);
        console.log(`🔐 Microsoft OAuth secret loaded: length=${secret.length}, fingerprint=${fingerprint}`);
      }
    }
  }

  /**
   * Check if provider is in demo mode (no real credentials configured)
   */
  isDemoMode(): boolean {
    return this.config.isDemoMode || false;
  }

  /**
   * Generate OAuth authorization URL
   */
  getAuthorizationUrl(redirectUri: string, state: string): string {
    let authorizeUrl = this.config.authorizeUrl;

    // Microsoft-specific: add tenant_id to URL
    if (this.provider === 'microsoft' && this.config.tenantId) {
      authorizeUrl = authorizeUrl.replace('{tenant_id}', this.config.tenantId);
    }

    const params = new URLSearchParams({
      client_id: this.config.clientId,
      redirect_uri: redirectUri,
      response_type: 'code',
      scope: this.config.scopes.join(' '),
      state,
    });

    return `${authorizeUrl}?${params.toString()}`;
  }

  /**
   * Exchange authorization code for access token
   */
  async exchangeCodeForToken(code: string, redirectUri: string): Promise<OAuthToken> {
    let tokenUrl = this.config.tokenUrl;

    // Microsoft-specific: add tenant_id to URL
    if (this.provider === 'microsoft' && this.config.tenantId) {
      tokenUrl = tokenUrl.replace('{tenant_id}', this.config.tenantId);
    }
    // Build form-encoded body required by providers (especially Microsoft)
    const form = new URLSearchParams();
    form.append('client_id', this.config.clientId);
    form.append('client_secret', this.config.clientSecret);
    form.append('code', code);
    form.append('redirect_uri', redirectUri);
    form.append('grant_type', 'authorization_code');
    // Microsoft requires scope again on token request for first exchange
    if (this.provider === 'microsoft') {
      form.append('scope', this.config.scopes.join(' '));
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/x-www-form-urlencoded'
    };
    if (this.provider === 'github') {
      headers['Accept'] = 'application/json';
    }

    let response;
    try {
      response = await axios.post(tokenUrl, form.toString(), { headers });
    } catch (err: any) {
      // Surface provider error details for troubleshooting
      if (axios.isAxiosError(err)) {
        const details = err.response?.data;
        console.error('OAuth token exchange failed:', {
          provider: this.provider,
          status: err.response?.status,
          data: details,
          url: tokenUrl,
        });
        // Special handling for common Microsoft secret error AADSTS7000215
        const desc = (details?.error_description || details?.error || err.message) as string;
        if (this.provider === 'microsoft' && /AADSTS7000215/i.test(desc)) {
          throw new Error('Invalid Microsoft client secret (AADSTS7000215). Use the secret VALUE (shown once) not the Secret ID. Generate a new secret under Certificates & secrets and update MICROSOFT_CLIENT_SECRET.');
        }
        throw new Error(desc);
      }
      throw err;
    }
    
    return {
      access_token: response.data.access_token,
      refresh_token: response.data.refresh_token,
      token_type: response.data.token_type || 'bearer',
      expires_in: response.data.expires_in || 3600,
      scope: response.data.scope,
    };
  }

  /**
   * Fetch user information from OAuth provider
   */
  async getUserInfo(accessToken: string): Promise<UserInfo> {
    const headers = {
      Authorization: `Bearer ${accessToken}`,
    };

    const response = await axios.get(this.config.userInfoUrl, { headers });
    const userData = response.data;

    // Normalize user data across providers
    if (this.provider === 'google') {
      return {
        id: userData.id,
        email: userData.email,
        name: userData.name || '',
        avatarUrl: userData.picture,
      };
    } else if (this.provider === 'github') {
      // GitHub requires separate call for email if not public
      let email = userData.email;
      if (!email) {
        const emailResponse = await axios.get('https://api.github.com/user/emails', { headers });
        const emails = emailResponse.data;
        const primaryEmail = emails.find((e: any) => e.primary);
        email = primaryEmail ? primaryEmail.email : emails[0]?.email;
      }

      return {
        id: String(userData.id),
        email,
        name: userData.name || userData.login,
        avatarUrl: userData.avatar_url,
      };
    } else if (this.provider === 'microsoft') {
      return {
        id: userData.id,
        email: userData.mail || userData.userPrincipalName,
        name: userData.displayName || '',
        avatarUrl: undefined,
      };
    }

    return {
      id: userData.id,
      email: userData.email,
      name: userData.name || '',
    };
  }
}

/**
 * JWT Manager
 * Handles JWT token creation and validation
 */
export class JWTManager {
  /**
   * Create JWT access token
   */
  static createAccessToken(user: User, expiresIn?: number): string {
    const expireMinutes = expiresIn || ACCESS_TOKEN_EXPIRE_MINUTES;
    const tokenId = crypto.randomBytes(32).toString('hex');

    const payload: any = {
      userId: user.id,
      email: user.email,
      provider: user.provider,
      roles: user.roles,
      exp: Math.floor(Date.now() / 1000) + expireMinutes * 60,
      iat: Math.floor(Date.now() / 1000),
      jti: tokenId,
      type: 'access',
    };

    return jwt.sign(payload, SECRET_KEY, { algorithm: ALGORITHM });
  }

  /**
   * Create JWT refresh token
   */
  static createRefreshToken(user: User): string {
    const expireDays = REFRESH_TOKEN_EXPIRE_DAYS;
    const tokenId = crypto.randomBytes(32).toString('hex');
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + expireDays);

    const payload: any = {
      userId: user.id,
      exp: Math.floor(expiresAt.getTime() / 1000),
      iat: Math.floor(Date.now() / 1000),
      jti: tokenId,
      type: 'refresh',
    };

    // Store refresh token
    tokenStore.storeRefreshToken(tokenId, user.id, expiresAt);

    return jwt.sign(payload, SECRET_KEY, { algorithm: ALGORITHM });
  }

  /**
   * Verify and decode JWT token
   */
  static async verifyToken(token: string, tokenType: 'access' | 'refresh' = 'access'): Promise<TokenData> {
    try {
      const payload = jwt.verify(token, SECRET_KEY, { algorithms: [ALGORITHM] }) as any;

      // Verify token type
      if (payload.type !== tokenType) {
        throw new Error(`Invalid token type. Expected ${tokenType}`);
      }

      // Check if token is revoked
      if (payload.jti && (await tokenStore.isRevoked(payload.jti))) {
        throw new Error('Token has been revoked');
      }

      return {
        userId: payload.userId,
        email: payload.email,
        provider: payload.provider,
        roles: payload.roles || ['user'],
        scopes: payload.scopes || [],
        exp: payload.exp,
        iat: payload.iat,
        jti: payload.jti,
      };
    } catch (error) {
      if (error instanceof jwt.TokenExpiredError) {
        throw new Error('Token has expired');
      }
      throw new Error(`Invalid token: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Refresh access token using refresh token
   */
  static async refreshAccessToken(refreshToken: string): Promise<TokenPair> {
    // Verify refresh token
    const tokenData = await JWTManager.verifyToken(refreshToken, 'refresh');

    // Validate refresh token in store
    const userId = await tokenStore.validateRefreshToken(tokenData.jti);
    if (!userId || userId !== tokenData.userId) {
      throw new Error('Invalid refresh token');
    }

    // Create new user object (in production, fetch from database)
    const user: User = {
      id: tokenData.userId,
      email: tokenData.email,
      name: '',
      provider: tokenData.provider,
      providerUserId: '',
      roles: tokenData.roles,
      isActive: true,
      createdAt: new Date(),
      lastLogin: new Date(),
    };

    // Generate new token pair with refresh token rotation
    const newAccessToken = JWTManager.createAccessToken(user);
    const newRefreshToken = JWTManager.createRefreshToken(user);

    // Revoke old refresh token
    await tokenStore.revokeToken(tokenData.jti);

    return {
      accessToken: newAccessToken,
      refreshToken: newRefreshToken,
      tokenType: 'bearer',
      expiresIn: ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    };
  }

  /**
   * Revoke a token
   */
  static async revokeToken(token: string): Promise<void> {
    try {
      const payload = jwt.decode(token) as any;
      if (payload?.jti) {
        await tokenStore.revokeToken(payload.jti);
      }
    } catch (error) {
      // Token is invalid, ignore
    }
  }
}

/**
 * Generate secure state token for OAuth CSRF protection
 */
export function generateStateToken(): string {
  return crypto.randomBytes(32).toString('hex');
}

/**
 * Hash token for secure storage
 */
export function hashToken(token: string): string {
  return crypto.createHash('sha256').update(token).digest('hex');
}

/**
 * Validate authorization header
 */
export function extractBearerToken(authHeader?: string): string | null {
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null;
  }
  return authHeader.substring(7);
}

/**
 * Role-based authorization checker
 */
export async function requireRoles(token: string, requiredRoles: string[]): Promise<TokenData> {
  const tokenData = await JWTManager.verifyToken(token);
  
  const hasRole = requiredRoles.some(role => tokenData.roles.includes(role));
  if (!hasRole) {
    throw new Error(`Insufficient permissions. Required roles: ${requiredRoles.join(', ')}`);
  }
  
  return tokenData;
}
