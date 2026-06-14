import type { TextareaHTMLAttributes } from "react";

interface TextareaFieldProps
  extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
}

export function TextareaField({ label, id, ...props }: TextareaFieldProps) {
  const fieldId = id ?? props.name ?? label;
  return (
    <label className="field" htmlFor={fieldId}>
      <span>{label}</span>
      <textarea id={fieldId} {...props} />
    </label>
  );
}
