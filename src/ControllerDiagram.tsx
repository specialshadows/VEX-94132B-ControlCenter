type Props = {selectedButton: string; onSelect: (button: string) => void};

/** V5 face layout: both sticks above the directional and letter diamonds. */
export function ControllerDiagram({selectedButton, onSelect}: Props) {
  const button = (name: string, position: string, display = name) => (
    <button type="button" key={name}
      className={`controller-input ${position}${selectedButton === name ? ' selected' : ''}`}
      aria-label={`Select ${name} button`} aria-pressed={selectedButton === name}
      title={name} onClick={() => onSelect(name)}>{display}</button>
  );
  return <div className="controller" role="group" aria-label="Interactive V5 controller button diagram">
    <svg className="controller-shell" viewBox="0 0 650 410" aria-hidden="true">
      <defs>
        <linearGradient id="controller-case" x2="0" y2="1">
          <stop stopColor="#384531"/><stop offset="1" stopColor="#1a241b"/>
        </linearGradient>
        <linearGradient id="controller-inlay" x2="0" y2="1">
          <stop stopColor="#536047"/><stop offset="1" stopColor="#303e2c"/>
        </linearGradient>
      </defs>
      <path className="controller-shadow" d="M143 65 Q325 6 507 65 Q571 92 589 171 Q618 273 602 349 Q593 398 550 382 Q514 368 493 310 Q479 283 443 283 H207 Q171 283 157 310 Q136 368 100 382 Q57 398 48 349 Q32 273 61 171 Q79 92 143 65Z"/>
      <path fill="url(#controller-case)" stroke="#768464" strokeWidth="2" d="M143 53 Q325 -6 507 53 Q571 80 589 159 Q618 261 602 337 Q593 386 550 370 Q514 356 493 298 Q479 271 443 271 H207 Q171 271 157 298 Q136 356 100 370 Q57 386 48 337 Q32 261 61 159 Q79 80 143 53Z"/>
      <path fill="url(#controller-inlay)" stroke="#69775a" d="M178 65 Q325 22 472 65 Q499 74 503 99 L525 210 Q530 250 483 253 H167 Q120 250 125 210 L147 99 Q151 74 178 65Z"/>
      <path fill="none" stroke="#536247" strokeWidth="2" d="M84 229 Q72 302 86 340 M566 229 Q578 302 564 340"/>
    </svg>
    <div className="controller-shoulder controller-shoulder-left">
      {button('L1', 'shoulder-button')}{button('L2', 'shoulder-button')}
    </div>
    <div className="controller-shoulder controller-shoulder-right">
      {button('R1', 'shoulder-button')}{button('R2', 'shoulder-button')}
    </div>
    <div className="controller-stick stick-left" aria-label="Left stick, Axis 3, forward">
      <span className="stick-cap"/><span className="stick-caption">AXIS 3 · FORWARD</span>
    </div>
    <div className="controller-screen" aria-hidden="true"><span>V5</span><strong>94132B</strong><i>CONTROL CENTER</i></div>
    <div className="controller-stick stick-right" aria-label="Right stick, Axis 1, steering">
      <span className="stick-cap"/><span className="stick-caption">AXIS 1 · STEERING</span>
    </div>
    <div className="controller-diamond dpad" role="group" aria-label="Directional pad">
      {button('Up', 'diamond-top', '▲')}{button('Left', 'diamond-left', '◀')}
      {button('Right', 'diamond-right', '▶')}{button('Down', 'diamond-bottom', '▼')}
    </div>
    <div className="controller-center-mark" aria-hidden="true">✧</div>
    <div className="controller-diamond face" role="group" aria-label="Letter buttons">
      {button('X', 'diamond-top')}{button('Y', 'diamond-left')}
      {button('A', 'diamond-right')}{button('B', 'diamond-bottom')}
    </div>
  </div>;
}
