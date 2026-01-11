import React, { useState, useEffect, useCallback, useRef } from "react";
import { useControl, useMap } from "react-map-gl";
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import "@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css";
import * as turf from "@turf/turf";
import { CheckCircle2, X, Crosshair, Layers, Trash2 } from "lucide-react";

const DrawControl = React.forwardRef((props: any, ref) => {
  useControl(
    () => new MapboxDraw(props),
    ({ map }) => {
      map.on("draw.create", props.onUpdate);
      map.on("draw.update", props.onUpdate);
      map.on("draw.delete", props.onDelete);
    },
    ({ map }) => {
      map.off("draw.create", props.onUpdate);
      map.off("draw.update", props.onUpdate);
      map.off("draw.delete", props.onDelete);
    },
    { position: props.position }
  );
  return null;
});

interface LandPlotterProps {
  onComplete: (data: any) => void;
  onCancel: () => void;
}

export default function LandPlotter({
  onComplete,
  onCancel,
}: LandPlotterProps) {
  const { current: map } = useMap();
  const [polygon, setPolygon] = useState<any>(null);
  const [stats, setStats] = useState({ acres: 0, plots: 0 });
  const [cursorTooltip, setCursorTooltip] = useState<{
    x: number;
    y: number;
    text: string;
  } | null>(null);
  const drawRef = useRef<MapboxDraw | null>(null);

  const calculateStats = useCallback((feature: any) => {
    if (!feature) {
      setStats({ acres: 0, plots: 0 });
      return;
    }
    const areaSqM = turf.area(feature);
    const areaSqFt = areaSqM * 10.7639;
    setStats({
      acres: areaSqFt / 43560,
      plots: areaSqFt / 4900, // Approx 70x70 plot
    });
  }, []);

  const onUpdate = useCallback(
    (e: any) => {
      const feature = e.features[0];
      setPolygon(feature);
      calculateStats(feature);
      setCursorTooltip(null);
    },
    [calculateStats]
  );

  const onDelete = useCallback(() => {
    setPolygon(null);
    setStats({ acres: 0, plots: 0 });
  }, []);

  // 🟢 UX FIX: Force Cursor Change & Tooltip
  useEffect(() => {
    if (!map) return;

    const canvas = map.getCanvas();
    canvas.style.cursor = "crosshair"; // Force cursor immediately

    const onMouseMove = (e: any) => {
      if (polygon) {
        canvas.style.cursor = "grab";
        return;
      }
      canvas.style.cursor = "crosshair";
      setCursorTooltip({
        x: e.point.x,
        y: e.point.y,
        text: "Click map to set boundary corner.",
      });
    };

    map.on("mousemove", onMouseMove);
    return () => {
      map.off("mousemove", onMouseMove);
      if (map && map.getCanvas()) {
        map.getCanvas().style.cursor = "";
      }
    };
  }, [map, polygon]);

  return (
    <>
      <DrawControl
        position="top-left"
        displayControlsDefault={false}
        controls={{ polygon: true, trash: true }}
        defaultMode="draw_polygon"
        onCreate={(draw: any) => {
          drawRef.current = draw;
        }}
        onUpdate={onUpdate}
        onDelete={onDelete}
      />

      {cursorTooltip && (
        <div
          className="fixed pointer-events-none z-[100] px-3 py-1.5 bg-emerald-600/90 text-white text-[10px] font-bold rounded-lg shadow-xl backdrop-blur-md border border-white/20 transform -translate-x-1/2 -translate-y-full mt-[-15px]"
          style={{ left: cursorTooltip.x, top: cursorTooltip.y }}
        >
          <div className="flex items-center gap-1">
            <Crosshair size={10} className="animate-spin-slow" />
            {cursorTooltip.text}
          </div>
        </div>
      )}

      {/* 🟢 UX FIX: pointer-events-auto enables interaction with this panel */}
      <div className="absolute top-20 left-4 z-50 flex flex-col gap-2 pointer-events-auto">
        <div className="bg-black/90 text-white p-4 rounded-xl border border-white/20 shadow-2xl backdrop-blur-xl min-w-[200px]">
          <div className="flex justify-between items-center mb-2 border-b border-white/10 pb-2">
            <h3 className="font-bold text-sm text-emerald-400 flex items-center gap-2">
              <Layers size={14} /> Land Registry
            </h3>
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X size={14} />
            </button>
          </div>

          <div className="space-y-1">
            <div className="text-2xl font-black">
              {stats.plots.toFixed(2)}{" "}
              <span className="text-xs font-normal text-gray-400">PLOTS</span>
            </div>
            <div className="text-xs text-gray-400 font-mono">
              {stats.acres.toFixed(3)} ACRES
            </div>
          </div>

          <div className="mt-4 flex gap-2">
            {!polygon ? (
              <div className="text-[10px] text-gray-400 italic flex items-center gap-2">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                Plotting Active...
              </div>
            ) : (
              <>
                <button
                  onClick={() => onComplete({ polygon, stats })}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white py-2 rounded-lg font-bold text-xs flex items-center justify-center gap-1 transition-colors"
                >
                  <CheckCircle2 size={12} /> SAVE
                </button>
                <button
                  onClick={() => {
                    if (drawRef.current) drawRef.current.deleteAll();
                    onDelete();
                  }}
                  className="p-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
