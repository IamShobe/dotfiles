// Machine-wide cap on concurrent `tsc` runs, loaded into every node process via
// NODE_OPTIONS=--require. Any process that is not tsc returns on the first check.
//
//   TSC_MAX_PARALLEL   slots shared by all tsc processes (default 3)
//
// TypeScript 7's launcher execve()s into the native compiler under the same pid,
// so the exit handler never runs there; the slot is reclaimed once that pid is dead.
const tscEntry = /[\\/]typescript[\\/](bin[\\/]tsc|lib[\\/]tsc\.js)$/

if (tscEntry.test(process.argv[1] ?? '')) waitForTscSlot()

function waitForTscSlot() {
  const fs = require('node:fs')
  const path = require('node:path')
  const os = require('node:os')

  const slotCount = Number(process.env.TSC_MAX_PARALLEL) || 3
  const slotsDir = path.join(os.homedir(), '.cache', 'tsc-slots')
  const pollMs = 500
  const sleeper = new Int32Array(new SharedArrayBuffer(4))
  fs.mkdirSync(slotsDir, { recursive: true })

  let announcedWait = false
  for (;;) {
    const slot = claimFreeSlot({ fs, path, slotsDir, slotCount })
    if (slot) {
      process.on('exit', () => releaseSlot({ fs, slot }))
      return
    }
    if (!announcedWait) {
      process.stderr.write(`tsc: waiting for one of ${slotCount} machine-wide slots (${slotsDir})\n`)
      announcedWait = true
    }
    Atomics.wait(sleeper, 0, 0, pollMs)
  }
}

function claimFreeSlot({ fs, path, slotsDir, slotCount }) {
  for (let index = 0; index < slotCount; index++) {
    const slot = path.join(slotsDir, `slot-${index}`)
    if (tryCreateSlot({ fs, slot })) return slot
    if (isHolderGone({ fs, slot })) {
      fs.rmSync(slot, { force: true })
      if (tryCreateSlot({ fs, slot })) return slot
    }
  }
  return undefined
}

function tryCreateSlot({ fs, slot }) {
  const claim = `${slot}.${process.pid}`
  fs.writeFileSync(claim, String(process.pid))
  try {
    fs.linkSync(claim, slot)
    return true
  } catch {
    return false
  } finally {
    fs.rmSync(claim, { force: true })
  }
}

function isHolderGone({ fs, slot }) {
  const holder = Number(readSlot({ fs, slot }))
  if (!holder) return true
  try {
    process.kill(holder, 0)
    return false
  } catch (error) {
    return error.code === 'ESRCH'
  }
}

function releaseSlot({ fs, slot }) {
  if (readSlot({ fs, slot }) === String(process.pid)) fs.rmSync(slot, { force: true })
}

function readSlot({ fs, slot }) {
  try {
    return fs.readFileSync(slot, 'utf8')
  } catch {
    return ''
  }
}
