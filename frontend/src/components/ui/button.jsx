// File: src/components/ui/button.jsx
import { cn } from "../../lib/utils";

export function Button({ children, className = "", ...props }) {
  return (
    <button
      className={cn(
        "bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700 transition",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
} 