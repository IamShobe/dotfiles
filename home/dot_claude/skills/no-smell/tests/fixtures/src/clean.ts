// switch (x) is mentioned in a comment only
/** switch (y) in jsdoc */
const label = user?.name ?? 'anon' ? 'a' : 'b';
const ok = flag ? 'on' : 'off';
const tpl = `${a ? 'x' : 'y'}-${b ? 'z' : 'w'}`;
export class NotFoundError extends Error {}
const run = runSchema.safeParse(JSON.parse(raw));
const env = z.object({ a: z.string() }).parse(JSON.parse(value));
const paths = Request.shape.s3InputPaths.parse(JSON.parse(env.S3));
const parsed: unknown = JSON.parse(text);
const raw = JSON.parse(text);
const result = payloadSchema.safeParse(raw);
const isMeta = key.startsWith(RESERVED_META_PREFIX);
const short = customerId.slice(0, 8);
const pairs = items.map((item, index) => [item, index]);
type Reducer = (acc: number, item: number) => number;
export function createLease({ customerId, ttlMs }: CreateLeaseInput) {}
const out = match(kind).otherwise(() => 1); // no-smell: kind is an open string from the CLI
class Counter { #count = 0 }
