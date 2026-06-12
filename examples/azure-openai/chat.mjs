// Your first Azure OpenAI call in Node.js (Chat Completions).
// Setup:
//   npm install openai
//   node --env-file=../../.env chat.mjs     (Node 20.6+ loads .env for you)
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: process.env.AZURE_OPENAI_ENDPOINT, // ends with /openai/v1/
  apiKey: process.env.AZURE_OPENAI_API_KEY,   // key from the organizers
});

const resp = await client.chat.completions.create({
  model: process.env.AZURE_OPENAI_CHAT_DEPLOYMENT || "gpt-5.5",
  messages: [{ role: "user", content: "Say hello to the hackathon in one line." }],
  max_completion_tokens: 2000, // gpt-5.x: use this, not max_tokens; no temperature
});

console.log(resp.choices[0].message.content);
