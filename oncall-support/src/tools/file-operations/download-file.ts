/**
 * File Operation Tool: Download File
 */
import { z } from "zod";
import fetch from "node-fetch";
import * as fs from "fs/promises";
import * as path from "path";

const MAX_DOWNLOAD_SIZE = parseInt(process.env.MAX_DOWNLOAD_SIZE || "104857600");
const LOCAL_STORAGE_DIR = process.env.LOCAL_STORAGE_DIR || "./oncall-files";

export const downloadFileTool = {
  name: "download-file",
  description: "Download a file from a URL to local storage",
  schema: {
    url: z.string().describe("URL of the file to download"),
    filename: z.string().optional().describe("Optional custom filename")
  },
  handler: async ({ url, filename }: { url: string; filename?: string }) => {
    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const contentLength = response.headers.get('content-length');
      if (contentLength && parseInt(contentLength) > MAX_DOWNLOAD_SIZE) {
        throw new Error(`File too large: ${contentLength} bytes (max: ${MAX_DOWNLOAD_SIZE})`);
      }

      const buffer = await response.buffer();
      const finalFilename = filename || path.basename(new URL(url).pathname) || "downloaded-file";
      const filePath = path.join(LOCAL_STORAGE_DIR, finalFilename);

      await fs.writeFile(filePath, buffer);

      return {
        content: [{
          type: "text",
          text: `File downloaded successfully:\n` +
            `- URL: ${url}\n` +
            `- Local path: ${filePath}\n` +
            `- Size: ${buffer.length} bytes`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: "text",
          text: `Error downloading file: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true
      };
    }
  }
};
