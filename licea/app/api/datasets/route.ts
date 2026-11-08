import catalog from '../../../server/seed.json';

// Published snapshots in Git are the only source of data. No database overrides.
export async function GET() {
  return Response.json({ catalog, revisions: {} }, {
    headers: { 'Cache-Control': 'no-store' },
  });
}
