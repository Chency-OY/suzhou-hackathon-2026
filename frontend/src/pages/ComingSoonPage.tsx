export default function ComingSoonPage({ title }: { title: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center">
      <div className="text-lg font-medium">{title}</div>
      <div className="mt-2 text-sm text-slate-500">该功能将在后续版本开放</div>
    </div>
  );
}
