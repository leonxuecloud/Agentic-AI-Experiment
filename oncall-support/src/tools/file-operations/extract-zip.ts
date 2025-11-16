/**
 * File Operation Tool: Extract ZIP
 */
import { z } from "zod";
import * as fs from "fs/promises";
import * as path from "path";
import AdmZip from "adm-zip";

export const extractZipTool = {
  name: "extract-zip",
  description: "Extract a ZIP file to a specified directory",
  schema: {
    zipPath: z.string().describe("Path to the ZIP file"),
    extractTo: z.string().optional().describe("Directory to extract to")
  },
  handler: async ({ zipPath, extractTo }: { zipPath: string; extractTo?: string }) => {
    try {
      const zip = new AdmZip(zipPath);
      const extractDir = extractTo || path.dirname(zipPath);

      await fs.mkdir(extractDir, { recursive: true });
      zip.extractAllTo(extractDir, true);

      const entries = zip.getEntries();
      const extractedFiles = entries.map(entry => entry.entryName);

      return {
        content: [{
          type: "text",
          text: `ZIP extracted successfully:\n` +
            `- Source: ${zipPath}\n` +
            `- Destination: ${extractDir}\n` +
            `- Files: ${extractedFiles.length}\n` +
            `- List: ${extractedFiles.join(", ")}`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: "text",
          text: `Error extracting ZIP: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true
      };
    }
  }
};
