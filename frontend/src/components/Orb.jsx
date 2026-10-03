import { useEffect, useRef } from "react";

export default function Orb({ state, getLevel }) {
  const coreRef = useRef(null);

  useEffect(() => {
    let raf, smooth = 0;
    const tick = () => {
      const target = state === "speaking" ? Math.min(getLevel() * 3, 1) : 0;
      smooth += (target - smooth) * 0.25; // smoothing avoids jitter
      if (coreRef.current) coreRef.current.style.transform = `scale(${1 + smooth * 0.6})`;
      raf = requestAnimationFrame(tick);
    };
    tick();
    return () => cancelAnimationFrame(raf);
  }, [state, getLevel]);

  return (
    <div className={`orb orb--${state}`}>
      <span className="ring r1" />
      <span className="ring r2" />
      <div className="core" ref={coreRef} />
    </div>
  );
}
