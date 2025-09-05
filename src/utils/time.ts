// src/utils/time.ts
export type TickLabels={year:string; day:string};

export function formatTicks(
  ticks:number,
  ticksPerDay=100,
  daysPerYear=365,
  labels:TickLabels={year:'Y', day:'D'}
):string{
  if(ticks<0) return '---';
  const totalDays=Math.floor(ticks/ticksPerDay);
  const year=Math.floor(totalDays/daysPerYear);
  const day=totalDays%daysPerYear;
  return `${labels.year}${year} ${labels.day}${day}`;
}

export function createTickFormatter(
  ticksPerDay=100,
  daysPerYear=365,
  labels:TickLabels={year:'Y', day:'D'}
){
  return (ticks:number)=>formatTicks(ticks, ticksPerDay, daysPerYear, labels);
}
