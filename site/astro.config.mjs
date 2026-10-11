// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

const SITE = 'https://ml.beehivewebstudio.com';
const OG_IMAGE = `${SITE}/og-image.png`;
const OG_ALT = 'open-data-ml: machine learning on openly licensed public data. First project: windml.';

// Fully static build for S3 + CloudFront. No SSR, no adapter, no third-party scripts.
export default defineConfig({
	site: SITE,
	output: 'static',
	trailingSlash: 'always',
	build: { format: 'directory' },
	integrations: [
		starlight({
			title: 'open-data-ml',
			description:
				'Machine learning on openly licensed public data, with every result published. First project: windml, wind turbine fault prediction and condition reports from open SCADA data.',
			favicon: '/favicon.svg',
			social: [
				{ icon: 'github', label: 'GitHub repository', href: 'https://github.com/7empestx/open-data-ml' },
				{ icon: 'email', label: 'Email hello@beehivewebstudio.com', href: 'mailto:hello@beehivewebstudio.com' },
			],
			head: [
				{ tag: 'link', attrs: { rel: 'icon', href: '/favicon.ico', sizes: '32x32' } },
				{ tag: 'link', attrs: { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' } },
				{ tag: 'meta', attrs: { name: 'theme-color', content: '#2f6b2e' } },
				{ tag: 'meta', attrs: { property: 'og:image', content: OG_IMAGE } },
				{ tag: 'meta', attrs: { property: 'og:image:width', content: '1200' } },
				{ tag: 'meta', attrs: { property: 'og:image:height', content: '630' } },
				{ tag: 'meta', attrs: { property: 'og:image:alt', content: OG_ALT } },
				{ tag: 'meta', attrs: { name: 'twitter:image', content: OG_IMAGE } },
				{ tag: 'meta', attrs: { name: 'twitter:image:alt', content: OG_ALT } },
			],
			customCss: ['./src/styles/custom.css'],
			lastUpdated: false,
			pagination: true,
			sidebar: [
				{ label: 'Home', link: '/' },
				{ label: 'Work with us', slug: 'work-with-us' },
				{
					label: 'windml',
					items: [
						{ label: 'Overview', slug: 'windml' },
						{ label: 'Results', slug: 'windml/results' },
						{ label: 'Sample condition report', slug: 'windml/condition-report' },
						{ label: 'Reproduce it', slug: 'windml/reproduce' },
						{ label: 'Data sources and licenses', slug: 'windml/data-sources' },
						{ label: 'Cleaning notes and data problems', slug: 'windml/cleaning' },
						{ label: 'Failure labels', slug: 'windml/labels' },
					],
				},
				{ label: 'About and data policy', slug: 'about' },
				{ label: 'Roadmap', slug: 'roadmap' },
			],
		}),
	],
});
