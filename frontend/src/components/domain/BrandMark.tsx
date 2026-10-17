import { Aperture } from "lucide-react";
import { Link } from "react-router-dom";

type Props = {
  to?: string | null;
};

export function BrandMark({ to = "/" }: Props) {
  const inner = (
    <>
      <span className="brand-mark" aria-hidden>
        <Aperture size={18} strokeWidth={2} />
      </span>
      <span>
        <div className="brand-wordmark">VIGILENS</div>
        <div className="brand-tag">A clearer lens on learning</div>
      </span>
    </>
  );

  if (to) {
    return (
      <Link className="brand" to={to}>
        {inner}
      </Link>
    );
  }

  return <div className="brand">{inner}</div>;
}
