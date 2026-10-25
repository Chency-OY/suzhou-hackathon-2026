import { DIFFICULTY_LABEL, DIFFICULTY_STYLE } from "../labels";
import type { Difficulty } from "../types";

export function DifficultyBadge({ value }: { value: Difficulty }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${DIFFICULTY_STYLE[value]}`}>
      {DIFFICULTY_LABEL[value]}
    </span>
  );
}

export function Tag({ children }: { children: React.ReactNode }) {
  return <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{children}</span>;
}
