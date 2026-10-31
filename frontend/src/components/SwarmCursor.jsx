import { useEffect, useRef } from 'react';
import './SwarmCursor.css';

// Lightweight React canvas adaptation of the supplied SwarmCursor API.
// It keeps the same main props and provides particle trails + click burst without WebGL.
export default function SwarmCursor({
  count = 800, size = 2.6, spread = 90, swirl = 0.6,
  clickEffect = 'burst', color = '#111827', accentColor = '#2583ff',
  enabled = true, children, className = '', style = {}, ...rest
}) {
  const hostRef = useRef(null);
  const canvasRef = useRef(null);
  const configRef = useRef({ count, size, spread, swirl, clickEffect, color, accentColor, enabled });
  configRef.current = { count, size, spread, swirl, clickEffect, color, accentColor, enabled };

  useEffect(() => {
    const host = hostRef.current, canvas = canvasRef.current;
    if (!host || !canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    let width = 1, height = 1, raf = 0, last = 0;
    const pointer = { x: 0, y: 0, inside: false };
    let particles = [];
    const cfg = () => configRef.current;
    const rand = (max) => Math.random() * max;
    const resize = () => {
      const rect = host.getBoundingClientRect();
      width = Math.max(1, rect.width); height = Math.max(1, rect.height);
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const n = Math.max(1, Math.min(2000, Math.round(cfg().count)));
      particles = Array.from({ length: n }, () => ({
        x: rand(width), y: rand(height), vx: rand(1.5) - .75, vy: rand(1.5) - .75,
        r: Math.max(.5, cfg().size * (.35 + Math.random())), phase: rand(Math.PI * 2)
      }));
    };
    const move = (e) => {
      const r = host.getBoundingClientRect();
      pointer.x = e.clientX - r.left; pointer.y = e.clientY - r.top;
      pointer.inside = pointer.x >= 0 && pointer.y >= 0 && pointer.x <= r.width && pointer.y <= r.height;
    };
    const leave = () => { pointer.inside = false; };
    const click = (e) => {
      if (!cfg().enabled || cfg().clickEffect === 'none') return;
      const r = host.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
      particles.forEach(p => {
        const dx = p.x - x, dy = p.y - y, d = Math.hypot(dx, dy) || 1;
        if (d < cfg().spread * 2.2) {
          const force = (1 - d / (cfg().spread * 2.2)) * (cfg().clickEffect === 'pulse' ? 5 : 14);
          p.vx += dx / d * force; p.vy += dy / d * force;
        }
      });
    };
    const frame = (now) => {
      raf = requestAnimationFrame(frame);
      const dt = Math.min(.033, (now - (last || now)) / 1000 || .016); last = now;
      if (!cfg().enabled || document.hidden) return;
      ctx.clearRect(0, 0, width, height);
      const c = cfg();
      particles.forEach((p) => {
        if (pointer.inside) {
          const dx = pointer.x - p.x, dy = pointer.y - p.y, d = Math.hypot(dx, dy) + .01;
          const influence = Math.exp(-(d * d) / (c.spread * c.spread * 2));
          p.vx += (dx / d * .7 - dy / d * c.swirl * .55) * influence;
          p.vy += (dy / d * .7 + dx / d * c.swirl * .55) * influence;
        } else {
          p.vx += Math.sin(now * .00035 + p.phase) * .025;
          p.vy += Math.cos(now * .0003 + p.phase) * .025;
        }
        p.vx *= .965; p.vy *= .965; p.x += p.vx * dt * 60; p.y += p.vy * dt * 60;
        if (p.x < 0) p.x = width; if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height; if (p.y > height) p.y = 0;
        const speed = Math.hypot(p.vx, p.vy);
        ctx.globalAlpha = .2 + Math.min(.65, speed * .06);
        ctx.fillStyle = speed > 2.2 ? c.accentColor : c.color;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
      });
      ctx.globalAlpha = 1;
    };
    const observer = new ResizeObserver(resize); observer.observe(host);
    window.addEventListener('pointermove', move, { passive: true });
    window.addEventListener('pointerdown', click, { passive: true });
    host.addEventListener('pointerleave', leave);
    resize(); raf = requestAnimationFrame(frame);
    return () => { cancelAnimationFrame(raf); observer.disconnect(); window.removeEventListener('pointermove', move); window.removeEventListener('pointerdown', click); host.removeEventListener('pointerleave', leave); };
  }, []);

  return <div ref={hostRef} className={`swarm-cursor ${className}`} style={style} {...rest}>
    <canvas ref={canvasRef} className="swarm-cursor-canvas" aria-hidden="true" />
    {children ? <div className="swarm-cursor-content">{children}</div> : null}
  </div>;
}
