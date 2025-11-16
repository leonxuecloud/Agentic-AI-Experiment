/**
 * File Operation Tool: List Local Files
 */
import { z } from "zod";
import * as fs from "fs/promises";
import * as path from "path";

const LOCAL_STORAGE_DIR = process.env.LOCAL_STORAGE_DIR || "./oncall-files";

export const listLocalFilesTool = {
  name: "list-local-files",
  description: "List files in the local storage directory",
  schema: {
    directory: z.string().optional().describe("Directory to list")
  },
  handler: async ({ directory }: { directory?: string }) => {
    try {
      const targetDir = directory || LOCAL_STORAGE_DIR;
      const files = await fs.readdir(targetDir, { withFileTypes: true });

      const fileList = files.map(file => ({
        name: file.name,
        type: file.isDirectory() ? "directory" : "file",
        path: path.join(targetDir, file.name)
      }));

      return {
        content: [{
          type: "text",
          text: `Files in ${targetDir}:\n\n` +
            fileList.map(file =>
              `${file.type === "directory" ? "📁" : "📄"} ${file.name}`
            ).join("\n")
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: "text",
          text: `Error listing files: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true
      };
    }
  }
};
