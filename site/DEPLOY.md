# Deploying open-data-ml to ml.beehivewebstudio.com (future steps, not run)

**Nothing here has been run.** No AWS command was executed, and none should be run until Grant approves. All commands run on Grant's own machine with his local AWS CLI credentials.

## 0. Build

The site (AstroWind on Astro 7) needs **Node.js 22.22.3 or newer**. The box's system Node is 20, so the site is built with a local Node 22 install.

```bash
cd site
npm ci
npm run build        # outputs fully static files to dist/
```

`astro.config.mjs` sets these options:
- `output: 'static'`, with no adapter and no SSR
- `site: 'https://ml.beehivewebstudio.com'`
- `trailingSlash: 'always'`
- `build.format: 'directory'`, so every page is `<path>/index.html`

## 1. One-time AWS setup (with Grant's approval)

Fill in your own values:
- `<bucket>`: for example `ml-beehivewebstudio-com-site`
- `<distribution-id>`
- `<account-id>`

### S3 bucket (private, CloudFront-only access)
- Create the bucket in any region, for example us-west-2. Keep **Block Public Access ON** and don't enable "static website hosting."
- Turn on default encryption (SSE-S3).

### CloudFront distribution with Origin Access Control (OAC)
- Origin: the bucket's REST endpoint (`<bucket>.s3.<region>.amazonaws.com`), not the website endpoint.
- Create an **OAC** (signing behavior "Always", SigV4) and attach it to the origin.
- Add the bucket policy CloudFront suggests. It allows `s3:GetObject` only for `cloudfront.amazonaws.com` with `AWS:SourceArn` equal to `arn:aws:cloudfront::<account-id>:distribution/<distribution-id>`.
- Default root object: `index.html`.
- Viewer protocol policy: Redirect HTTP to HTTPS. Compression on. Use the managed `CachingOptimized` cache policy.
- **Subdirectory index rewrite.** With OAC, CloudFront only serves `index.html` at the root. Add a **CloudFront Function** (viewer request) so `/windml/labels/` maps to `/windml/labels/index.html`:

```js
function handler(event) {
  var req = event.request;
  var uri = req.uri;
  if (uri.endsWith('/')) {
    req.uri = uri + 'index.html';
  } else if (!uri.split('/').pop().includes('.')) {
    // no trailing slash and no file extension: redirect to the slash version
    return { statusCode: 301, statusDescription: 'Moved Permanently',
             headers: { location: { value: uri + '/' } } };
  }
  return req;
}
```

- Custom error response: 403 and 404 map to `/404.html` with status 404. A private S3 bucket returns 403 for missing keys.
- Alternate domain name (CNAME): `ml.beehivewebstudio.com`.

### ACM certificate (must be in us-east-1)
- Request a public certificate for `ml.beehivewebstudio.com` in **us-east-1 (N. Virginia)**. CloudFront only accepts certificates from that region.
- Validate it by DNS: add the CNAME record ACM gives you at your DNS provider.
- Attach the certificate to the distribution.

### DNS
- At the DNS provider for `beehivewebstudio.com`, add **`ml` CNAME `<distribution-domain>.cloudfront.net`**.
- If the zone is in Route 53, use an **A/AAAA alias** to the distribution instead.

## 2. Deploy (each release)

```bash
# from site/ after npm run build
aws s3 sync dist/ s3://<bucket> --delete

# optional: longer cache for hashed assets, short cache for HTML
aws s3 cp s3://<bucket>/_astro/ s3://<bucket>/_astro/ --recursive \
  --metadata-directive REPLACE --cache-control "public,max-age=31536000,immutable"

# invalidate so CloudFront serves the new HTML
aws cloudfront create-invalidation --distribution-id <distribution-id> --paths "/*"
```

Add `--profile <profile>` to each command if Grant uses a named AWS CLI profile.

## 3. Check after deploying
- https://ml.beehivewebstudio.com/ loads over HTTPS.
- `/windml/labels/` and `/windml/labels` (which should redirect) both work.
- A made-up path returns the 404 page.
- There is no site search in the AstroWind version (Starlight's Pagefind search was removed). Navigation is the header, footer and docs sidebar.

## Cost note (est.)
For a small static site, S3 storage and CloudFront traffic are typically a few dollars a month or less. The ACM public certificate is free. CloudFront Functions are billed per invocation at a very low rate.
