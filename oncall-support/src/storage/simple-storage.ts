/**
 * Simple File-Based Storage
 * 
 * Lightweight storage for sessions and audit logs without database complexity.
 * Perfect for single-user MCP server deployment.
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { existsSync } from 'fs';

const STORAGE_DIR = process.env.STORAGE_DIR || './.mcp-storage';
const SESSIONS_FILE = path.join(STORAGE_DIR, 'sessions.json');
const AUDIT_LOG_FILE = path.join(STORAGE_DIR, 'audit.log');
const USERS_FILE = path.join(STORAGE_DIR, 'users.json');

// Initialize storage directory
async function ensureStorageExists(): Promise<void> {
  try {
    if (!existsSync(STORAGE_DIR)) {
      await fs.mkdir(STORAGE_DIR, { recursive: true });
    }
  } catch (error) {
    console.error('Failed to create storage directory:', error);
  }
}

// Session Management (In-Memory with File Backup)
interface Session {
  userId: string;
  email: string;
  name: string;
  provider: string;
  roles: string[];
  refreshToken: string;
  expiresAt: Date;
  createdAt: Date;
}

class SessionStore {
  private sessions: Map<string, Session> = new Map();
  private initialized = false;

  async init(): Promise<void> {
    if (this.initialized) return;
    
    await ensureStorageExists();
    
    // Load sessions from file if exists
    try {
      if (existsSync(SESSIONS_FILE)) {
        const data = await fs.readFile(SESSIONS_FILE, 'utf-8');
        const sessions: [string, Session][] = JSON.parse(data);
        
        // Filter out expired sessions
        const now = new Date();
        sessions.forEach(([key, session]) => {
          const expiresAt = new Date(session.expiresAt);
          if (expiresAt > now) {
            session.expiresAt = expiresAt; // Convert back to Date object
            session.createdAt = new Date(session.createdAt);
            this.sessions.set(key, session);
          }
        });
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
    
    this.initialized = true;
  }

  async save(userId: string, session: Session): Promise<void> {
    this.sessions.set(userId, session);
    await this.persist();
  }

  async get(userId: string): Promise<Session | undefined> {
    const session = this.sessions.get(userId);
    if (session && new Date(session.expiresAt) > new Date()) {
      return session;
    }
    // Remove expired session
    if (session) {
      this.sessions.delete(userId);
      await this.persist();
    }
    return undefined;
  }

  async getByRefreshToken(refreshToken: string): Promise<Session | undefined> {
    for (const session of this.sessions.values()) {
      if (session.refreshToken === refreshToken && new Date(session.expiresAt) > new Date()) {
        return session;
      }
    }
    return undefined;
  }

  async delete(userId: string): Promise<void> {
    this.sessions.delete(userId);
    await this.persist();
  }

  async cleanup(): Promise<void> {
    const now = new Date();
    let changed = false;
    
    for (const [key, session] of this.sessions.entries()) {
      if (new Date(session.expiresAt) <= now) {
        this.sessions.delete(key);
        changed = true;
      }
    }
    
    if (changed) {
      await this.persist();
    }
  }

  private async persist(): Promise<void> {
    try {
      const data = JSON.stringify(Array.from(this.sessions.entries()), null, 2);
      await fs.writeFile(SESSIONS_FILE, data, 'utf-8');
    } catch (error) {
      console.error('Failed to persist sessions:', error);
    }
  }
}

// User Management (Simple File-Based)
interface User {
  id: string;
  email: string;
  name: string;
  avatarUrl?: string;
  provider: string;
  roles: string[];
  createdAt: Date;
  lastLogin: Date;
}

class UserStore {
  private users: Map<string, User> = new Map();
  private initialized = false;

  async init(): Promise<void> {
    if (this.initialized) return;
    
    await ensureStorageExists();
    
    // Load users from file if exists
    try {
      if (existsSync(USERS_FILE)) {
        const data = await fs.readFile(USERS_FILE, 'utf-8');
        const users: User[] = JSON.parse(data);
        users.forEach(user => {
          user.createdAt = new Date(user.createdAt);
          user.lastLogin = new Date(user.lastLogin);
          this.users.set(user.id, user);
        });
      }
    } catch (error) {
      console.error('Failed to load users:', error);
    }
    
    this.initialized = true;
  }

  async findByEmail(email: string): Promise<User | undefined> {
    for (const user of this.users.values()) {
      if (user.email === email) {
        return user;
      }
    }
    return undefined;
  }

  async findById(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async create(userData: Omit<User, 'createdAt' | 'lastLogin'>): Promise<User> {
    const user: User = {
      ...userData,
      createdAt: new Date(),
      lastLogin: new Date(),
    };
    this.users.set(user.id, user);
    await this.persist();
    return user;
  }

  async update(id: string, updates: Partial<User>): Promise<User | undefined> {
    const user = this.users.get(id);
    if (!user) return undefined;
    
    const updated = { ...user, ...updates };
    this.users.set(id, updated);
    await this.persist();
    return updated;
  }

  async all(): Promise<User[]> {
    return Array.from(this.users.values());
  }

  private async persist(): Promise<void> {
    try {
      const data = JSON.stringify(Array.from(this.users.values()), null, 2);
      await fs.writeFile(USERS_FILE, data, 'utf-8');
    } catch (error) {
      console.error('Failed to persist users:', error);
    }
  }
}

// Audit Logging (Append-Only File)
interface AuditLogEntry {
  timestamp: string;
  userId?: string;
  action: string;
  resource: string;
  resourceId?: string;
  status: 'success' | 'failure';
  ipAddress?: string;
  userAgent?: string;
  details?: string;
}

class AuditLogger {
  private initialized = false;

  async init(): Promise<void> {
    if (this.initialized) return;
    await ensureStorageExists();
    this.initialized = true;
  }

  async log(entry: Omit<AuditLogEntry, 'timestamp'>): Promise<void> {
    const logEntry: AuditLogEntry = {
      timestamp: new Date().toISOString(),
      ...entry,
    };

    const logLine = JSON.stringify(logEntry) + '\n';

    try {
      await fs.appendFile(AUDIT_LOG_FILE, logLine, 'utf-8');
    } catch (error) {
      console.error('Failed to write audit log:', error);
    }
  }

  async getLogs(options?: {
    limit?: number;
    userId?: string;
    action?: string;
    startDate?: Date;
    endDate?: Date;
  }): Promise<AuditLogEntry[]> {
    try {
      if (!existsSync(AUDIT_LOG_FILE)) {
        return [];
      }

      const data = await fs.readFile(AUDIT_LOG_FILE, 'utf-8');
      const lines = data.trim().split('\n').filter(line => line.trim());
      
      let logs: AuditLogEntry[] = lines.map(line => JSON.parse(line));

      // Apply filters
      if (options?.userId) {
        logs = logs.filter(log => log.userId === options.userId);
      }
      if (options?.action) {
        logs = logs.filter(log => log.action === options.action);
      }
      if (options?.startDate) {
        logs = logs.filter(log => new Date(log.timestamp) >= options.startDate!);
      }
      if (options?.endDate) {
        logs = logs.filter(log => new Date(log.timestamp) <= options.endDate!);
      }

      // Sort by timestamp descending (newest first)
      logs.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

      // Apply limit
      if (options?.limit) {
        logs = logs.slice(0, options.limit);
      }

      return logs;
    } catch (error) {
      console.error('Failed to read audit logs:', error);
      return [];
    }
  }

  async rotate(): Promise<void> {
    // Rotate log file when it gets too large (>10MB)
    try {
      const stats = await fs.stat(AUDIT_LOG_FILE);
      if (stats.size > 10 * 1024 * 1024) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const archivePath = path.join(STORAGE_DIR, `audit-${timestamp}.log`);
        await fs.rename(AUDIT_LOG_FILE, archivePath);
        console.log(`Rotated audit log to: ${archivePath}`);
      }
    } catch (error) {
      // File doesn't exist or other error - ignore
    }
  }
}

// Export singleton instances
export const sessionStore = new SessionStore();
export const userStore = new UserStore();
export const auditLogger = new AuditLogger();

// Initialize all stores
export async function initializeStorage(): Promise<void> {
  await sessionStore.init();
  await userStore.init();
  await auditLogger.init();
  
  // Setup cleanup interval (every hour)
  setInterval(async () => {
    await sessionStore.cleanup();
    await auditLogger.rotate();
  }, 60 * 60 * 1000);
}

// Export types
export type { Session, User, AuditLogEntry };
