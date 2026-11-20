import { Fragment } from "react";

// Lets long source paths wrap after each "/" instead of mid-word. <wbr> adds
// no text, so the path reads and copies exactly as in the source.
export default function FieldPath({ path }: { path: string }) {
  const parts = path.split("/");
  return (
    <>
      {parts.map((part, index) => (
        <Fragment key={index}>
          {part}
          {index < parts.length - 1 && (
            <>
              /<wbr />
            </>
          )}
        </Fragment>
      ))}
    </>
  );
}
