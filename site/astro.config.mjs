// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// Fully static build for S3 + CloudFront. No SSR, no adapter.
export default defineConfig({
	site: 'https://ml.beehivewebstudio.com',
	output: 'static',
	trailingSlash: 'always',
	build: { format: 'directory' },
	integrations: [
		starlight({
			title: 'open-data-ml',
			description: 'Machine learning on openly licensed public data. First project: windml, wind turbine fault detection on open SCADA data.',
			customCss: ['./src/styles/custom.css'],
			lastUpdated: false,
			pagination: true,
			sidebar: [
				{ label: 'About and data policy', slug: 'about' },
				{
					label: 'windml',
					items: [
						{ label: 'Overview', slug: 'windml' },
						{ label: 'Data sources and licenses', slug: 'windml/data-sources' },
						{ label: 'Cleaning notes and data problems', slug: 'windml/cleaning' },
						{ label: 'Failure labels', slug: 'windml/labels' },
						{ label: 'Results', slug: 'windml/results' },
						{ label: 'Sample condition report', slug: 'windml/condition-report' },
					],
				},
				{ label: 'Roadmap', slug: 'roadmap' },
			],
		}),
	],
});
