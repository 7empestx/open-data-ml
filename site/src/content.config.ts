import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';

// Long-form pages (windml docs, about, roadmap). The homepage, Work with us and 404 are Astro pages.
const docs = defineCollection({
  loader: glob({ pattern: ['**/*.{md,mdx}'], base: './src/content/docs' }),
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
  }),
});

export const collections = { docs };
