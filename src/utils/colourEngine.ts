// src/utils/colourEngine.ts
export type EQType = 'user'|'bby'|'red'|'green'|'blue'|'rainbow';
export type RgbColor = { r: number; g: number; b: number };

export type StepContext = {
  activeEqs: Set<EQType>;
  userColour: RgbColor;
  bbyColour: RgbColor;
  tempo: number;

  userColorInfluence: number;
  bbyInfluence: number;
  redInfluence: number;
  greenInfluence: number;
  blueInfluence: number;
  rainbowInfluence: number;

  baseStep?: number;       // default 0.08
  rainbowHueStep?: number; // default 20°
};

export function clampByte(x:number){ return Math.max(0, Math.min(255, Math.round(x))); }

export function hexToRGB(hx: string): RgbColor {
  let h = hx.replace('#', '');
  if (h.length === 3) {
    h = h.split('').map(c => c + c).join('');
  }
  if (h.length !== 6) {
    throw new Error(`Invalid hex colour: ${hx}`);
  }
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  };
}

export function rgbToHsv(r:number,g:number,b:number){
  r/=255; g/=255; b/=255;
  const mx=Math.max(r,g,b), mn=Math.min(r,g,b), d=mx-mn;
  let h=0;
  if(d){
    if(mx===r) h=((g-b)/d)%6;
    else if(mx===g) h=(b-r)/d+2;
    else h=(r-g)/d+4;
    h*=60; if(h<0) h+=360;
  }
  const s = mx===0?0:d/mx;
  return { h, s, v: mx };
}

export function hsvToRgb(h:number,s:number,v:number){
  const c=v*s, x=c*(1-Math.abs(((h/60)%2)-1)), m=v-c;
  let R=0,G=0,B=0;
  h%=360; if(h<0) h+=360;
  if (0<=h && h<60)   [R,G,B]=[c,x,0];
  else if (h<120)     [R,G,B]=[x,c,0];
  else if (h<180)     [R,G,B]=[0,c,x];
  else if (h<240)     [R,G,B]=[0,x,c];
  else if (h<300)     [R,G,B]=[x,0,c];
  else                [R,G,B]=[c,0,x];
  return { r: clampByte((R+m)*255), g: clampByte((G+m)*255), b: clampByte((B+m)*255) };
}

/** ONE deterministic brush step — use this in both scope + brush */
export function stepColourOnce(c: RgbColor, ctx: StepContext): RgbColor {
  const {
    activeEqs, userColour, bbyColour, tempo,
    userColorInfluence, bbyInfluence, redInfluence, greenInfluence, blueInfluence, rainbowInfluence,
    baseStep = 0.08, rainbowHueStep = 20
  } = ctx;

  const step = baseStep * (tempo / 120);

  const { h, s, v } = rgbToHsv(c.r, c.g, c.b);
  const rVec   = { r: 255 - c.r, g: -c.g,        b: -c.b        };
  const gVec   = { r: -c.r,      g: 255 - c.g,   b: -c.b        };
  const bVec   = { r: -c.r,      g: -c.g,        b: 255 - c.b   };
  const uVec   = { r: userColour.r - c.r, g: userColour.g - c.g, b: userColour.b - c.b };
  const bbyVec = { r: bbyColour.r  - c.r, g: bbyColour.g  - c.g, b: bbyColour.b  - c.b };
  const rbwT   = hsvToRgb((h + rainbowHueStep) % 360, s, v);
  const rbwVec = { r: rbwT.r - c.r, g: rbwT.g - c.g, b: rbwT.b - c.b };

  let dR=0, dG=0, dB=0;
  if (activeEqs.has('user'))    { dR += uVec.r   * (userColorInfluence / 100); dG += uVec.g   * (userColorInfluence / 100); dB += uVec.b   * (userColorInfluence / 100); }
  if (activeEqs.has('bby'))     { dR += bbyVec.r * (bbyInfluence     / 100);   dG += bbyVec.g * (bbyInfluence     / 100);   dB += bbyVec.b * (bbyInfluence     / 100); }
  if (activeEqs.has('red'))     { dR += rVec.r   * (redInfluence     / 100);   dG += rVec.g   * (redInfluence     / 100);   dB += rVec.b   * (redInfluence     / 100); }
  if (activeEqs.has('green'))   { dR += gVec.r   * (greenInfluence   / 100);   dG += gVec.g   * (greenInfluence   / 100);   dB += gVec.b   * (greenInfluence   / 100); }
  if (activeEqs.has('blue'))    { dR += bVec.r   * (blueInfluence    / 100);   dG += bVec.g   * (blueInfluence    / 100);   dB += bVec.b   * (blueInfluence    / 100); }
  if (activeEqs.has('rainbow')) { dR += rbwVec.r * (rainbowInfluence / 100);   dG += rbwVec.g * (rainbowInfluence / 100);   dB += rbwVec.b * (rainbowInfluence / 100); }

  return {
    r: clampByte(c.r + dR * step),
    g: clampByte(c.g + dG * step),
    b: clampByte(c.b + dB * step),
  };
}

/** Next N colours starting from a hex or RGB */
export function computeNextColours(n: number, start: RgbColor | string, ctx: StepContext): RgbColor[] {
  let c: RgbColor = typeof start === 'string' ? hexToRGB(start) : { ...start };
  const out: RgbColor[] = [];
  for (let i = 0; i < n; i++) { c = stepColourOnce(c, ctx); out.push({ ...c }); }
  return out;
}
