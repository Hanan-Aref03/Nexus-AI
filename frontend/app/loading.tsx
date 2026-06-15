export default function Loading() {
  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-white/8 bg-white/5 p-6">
        <div className="h-4 w-40 rounded-full bg-white/10" />
        <div className="mt-4 h-10 w-3/4 rounded-2xl bg-white/10" />
        <div className="mt-3 h-4 w-full rounded-full bg-white/10" />
      </div>

      <div className="grid gap-4 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-32 animate-pulse rounded-3xl border border-white/8 bg-white/5" />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr,0.8fr]">
        <div className="h-[520px] animate-pulse rounded-3xl border border-white/8 bg-white/5" />
        <div className="h-[520px] animate-pulse rounded-3xl border border-white/8 bg-white/5" />
      </div>
    </div>
  );
}
