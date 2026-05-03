export function StartStatusBar() {
  return (
    <div className="fixed bottom-5 right-5 hidden gap-6 text-[#9a8f84] lg:flex">
      <span className="flex items-center gap-2">
        <span className="h-2 w-2 rounded-full bg-[#bac8dc]" />
        <span className="font-mono text-[10px] uppercase tracking-widest">System core active</span>
      </span>
      <span className="font-mono text-[10px] uppercase tracking-widest">Ready</span>
    </div>
  );
}
