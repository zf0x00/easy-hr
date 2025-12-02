#!/usr/bin/env node
// scripts/start_parallax_cluster.js
// Cross-platform launcher for parallax run + parallax join

const { spawn } = require('child_process');
const path = require('path');
const os = require('os');

const PARALLAX_DIR = process.env.PARALLAX_DIR || path.join(os.homedir(), 'parallax');
const isWin = process.platform === 'win32';
const venvBin = isWin ? path.join(PARALLAX_DIR, 'venv', 'Scripts') : path.join(PARALLAX_DIR, 'venv', 'bin');
const parallaxExec = isWin ? path.join(venvBin, 'parallax.exe') : path.join(venvBin, 'parallax');

function exists(p) {
  const fs = require('fs');
  try { return fs.existsSync(p); } catch { return false; }
}

if (!exists(parallaxExec)) {
  console.error(`parallax executable not found at ${parallaxExec}`);
  console.error('Either create the venv in the parallax folder or set PARALLAX_DIR env var to the correct location.');
  process.exit(1);
}

function spawnCmd(cmd, args, name) {
  const ps = spawn(cmd, args, { stdio: ['ignore', 'pipe', 'pipe'] });
  ps.stdout.on('data', d => process.stdout.write(`[${name}] ${d.toString()}`));
  ps.stderr.on('data', d => process.stderr.write(`[${name} ERR] ${d.toString()}`));
  ps.on('exit', (code) => console.log(`[${name}] exited with ${code}`));
  return ps;
}

// scheduler (UI)
const schedArgs = ['run', '--host', '0.0.0.0', '--port', '3001', '-u'];
console.log('Starting parallax scheduler...');
const sched = spawnCmd(parallaxExec, schedArgs, 'scheduler');

// small delay then join
setTimeout(() => {
  console.log('Starting parallax join (node)...');
  const join = spawnCmd(parallaxExec, ['join', '-u'], 'join');

  // graceful shutdown on ctrl+c
  process.on('SIGINT', () => {
    console.log('Shutting down child processes...');
    [sched, join].forEach(p => p && !p.killed && p.kill('SIGTERM'));
    process.exit();
  });
}, 2000);
