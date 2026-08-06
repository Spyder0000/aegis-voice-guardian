import React, { useEffect, useRef, useState } from "react";

/**
 * VoiceOrb component — lightweight native Web Audio API visualizer.
 * Reads real-time microphone volume without heavy WebGL / external libraries.
 */
export default function VoiceOrb({ listening = false }) {
  const [scale, setScale] = useState(1.0);
  const [volume, setVolume] = useState(0);
  const animationFrameRef = useRef(null);
  const audioContextRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    if (!listening) {
      cleanupAudio();
      setScale(1.0);
      setVolume(0);
      return;
    }

    let isSubscribed = true;

    async function initAudio() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        if (!isSubscribed) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        streamRef.current = stream;

        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) {
          return;
        }

        const audioCtx = new AudioCtx();
        audioContextRef.current = audioCtx;

        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);

        const dataArray = new Uint8Array(analyser.frequencyBinCount);

        function updateVolume() {
          if (!isSubscribed) return;

          analyser.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
          }
          const avg = sum / dataArray.length;
          const normVolume = Math.min(1.0, avg / 128.0);

          setVolume(normVolume);
          // Scale mapped smoothly between 1.0 and 1.3
          setScale(1.0 + normVolume * 0.3);

          animationFrameRef.current = requestAnimationFrame(updateVolume);
        }

        updateVolume();
      } catch (err) {
        console.warn("Microphone access denied or unavailable:", err);
      }
    }

    initAudio();

    return () => {
      isSubscribed = false;
      cleanupAudio();
    };
  }, [listening]);

  function cleanupAudio() {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      if (audioContextRef.current.state !== "closed") {
        audioContextRef.current.close().catch(() => {});
      }
      audioContextRef.current = null;
    }
  }

  const glowBlur = Math.round(15 + volume * 45);
  const glowSpread = Math.round(5 + volume * 25);

  return (
    <div className="voice-orb-wrapper">
      <div
        className={`voice-orb ${listening ? "voice-orb--active" : "voice-orb--idle"}`}
        style={{
          transform: `scale(${scale})`,
          boxShadow: listening
            ? `0 0 ${glowBlur}px ${glowSpread}px var(--primary-glow, rgba(147, 51, 234, 0.45)), inset 0 0 20px rgba(255, 255, 255, 0.2)`
            : `0 0 15px 2px rgba(255, 255, 255, 0.08)`,
        }}
      >
        <div className="voice-orb__inner" />
      </div>
      <p className="voice-orb__label">
        {listening ? (
          <span className="voice-orb__status voice-orb__status--listening">
            <span className="pulse-dot" /> Listening...
          </span>
        ) : (
          <span className="voice-orb__status voice-orb__status--idle">Microphone idle</span>
        )}
      </p>
    </div>
  );
}
