import { b } from "../baml_client";
import type { Resume } from "../baml_client/types";

/**
 * Example function using BAML to extract resume information
 */
async function extractResumeExample(rawResume: string): Promise<Resume> {
  // Call the BAML ExtractResume function
  const response = await b.ExtractResume(rawResume);
  return response;
}

/**
 * Example function using BAML stream to extract resume information
 */
async function extractResumeStreamExample(rawResume: string): Promise<Resume> {
  const stream = b.stream.ExtractResume(rawResume);
  
  // Process partial results as they come in
  for await (const msg of stream) {
    console.log("Partial result:", msg);
  }

  // Get the final complete response
  return await stream.getFinalResponse();
}

// Example resume text
const sampleResume = `
John Doe
john.doe@example.com

Experience:
- Senior Developer at Tech Company
- Software Engineer at Startup
- Intern at Big Corp

Skills:
- JavaScript
- TypeScript
- React
- Node.js
`;

// Example usage (commented out to avoid execution)
/*
async function runExample() {
  try {
    // Make sure OPENAI_API_KEY is set in your environment variables
    console.log("Extracting resume...");
    const resume = await extractResumeExample(sampleResume);
    console.log("Extracted resume:", resume);
    
    console.log("\nExtracting resume with streaming...");
    const streamedResume = await extractResumeStreamExample(sampleResume);
    console.log("Final streamed resume:", streamedResume);
  } catch (error) {
    console.error("Error extracting resume:", error);
  }
}

runExample();
*/

export { extractResumeExample, extractResumeStreamExample };