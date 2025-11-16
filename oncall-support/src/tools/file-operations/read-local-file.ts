/**
 * File Operation Tool: Read Local File
 */
import { z } from "zod";
import * as fs from "fs/promises";

export const readLocalFileTool = {
  name: "read-local-file",
  description: "Read the contents of a local file",
  schema: {
    filePath: z.string().describe("Path to the file"),
    maxLines: z.number().optional().describe("Maximum lines to read")
  },
  handler: async ({ filePath, maxLines }: { filePath: string; maxLines?: number }) => {
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      const lines = content.split('\n');
      const displayLines = maxLines ? lines.slice(0, maxLines) : lines;
      const truncated = maxLines && lines.length > maxLines;

      return {
        content: [{
          type: "text",
          text: `File: ${filePath}\n` +
            `Size: ${content.length} chars, ${lines.length} lines\n` +
            (truncated ? `(Showing first ${maxLines} lines)\n` : "") +
            `\nContent:\n${displayLines.join('\n')}` +
            (truncated ? `\n\n... (${lines.length - maxLines} more lines)` : "")
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: "text",
          text: `Error reading file: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true
      };
    }
  }
};
