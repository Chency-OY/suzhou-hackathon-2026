import { DIFFICULTY_LABEL } from "../labels";
import type { Difficulty } from "../types";

export function DifficultyBadge({ value }: { value: Difficulty }) {
  return (
    <span className={`game-tag game-${value}`}>
      {DIFFICULTY_LABEL[value]}
    </span>
  );
}

export function Tag({ children }: { children: React.ReactNode }) {
  return <span className="game-tag">{children}</span>;
}
