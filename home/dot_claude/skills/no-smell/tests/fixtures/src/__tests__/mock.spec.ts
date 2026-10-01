vi.mocked(fn).mockResolvedValue({ a: 1 } as any);
const p = JSON.parse(body);
