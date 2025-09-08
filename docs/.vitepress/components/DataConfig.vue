<script setup>
import { ref, computed, onMounted, watchEffect } from 'vue'

const selections = ref({
  channels: ['ttbar'],
  pileup: ['pileup-10'],
  objects: ['tracks'],
  processing: {
    merge: false,
    pytorch: false
  },
  eventCount: 1000 // Default value
})

const expanded = ref({
  channels: false,
  pileup: false,
  objects: false
})

// Datasets (derived from manifest)
const channelTypes = ref([])

const pileupTypes = ref([
  { id: 'single_particle', label: 'Single Particle', available: false },
  { id: 'pileup-10', label: '<μ>=10', available: false },
  { id: 'pileup-200', label: '<μ>=200', available: false }
])

// Objects (derived from manifest)
const objectTypes = ref([])

// Manifest fetch + derivation
// Use bundled manifest (fetched during CI build) to avoid CORS
const manifestUrlCandidates = [
  '/manifest.json'  // bundled by CI from NERSC portal
]
const manifest = ref(null)
const selectedCampaign = ref('taster')

// Approximate display sizes per object (GB per 1,000 events)
const objectDisplaySizes = {
  hits: 10,
  tracks: 0.1,
  particle_flow: 20,
  particles: 3,
  events: 1,
  partons: 2,
  tracker_hits: 10,
  calo_cells: 30
}

const now = () => new Date()

function deriveFromManifest() {
  if (!manifest.value) return
  const campaigns = manifest.value.campaigns || {}
  const camp = campaigns[selectedCampaign.value]
  if (!camp || !camp.datasets) return

  // Diagnostics: log high-level manifest details for visibility
  try {
    console.log('[ColliderML] campaigns:', Object.keys(campaigns))
    console.log('[ColliderML] selected campaign:', selectedCampaign.value, { pileup: camp.pileup, default: camp.default })
  } catch {}

  // Pileup from campaign if present; enable corresponding pileup button
  // Expect e.g. { pileup: 200 } -> select 'pileup-200'
  if (camp.pileup) {
    const pid = `pileup-${camp.pileup}`
    pileupTypes.value = pileupTypes.value.map(p => ({ ...p, available: p.id === pid }))
    // Initialize selection to campaign pileup if not already selected
    if (!selections.value.pileup.includes(pid)) {
      selections.value.pileup = [pid]
    }
  }

  // Datasets list
  const datasets = Object.keys(camp.datasets)
  console.log('[ColliderML] datasets in campaign', selectedCampaign.value, ':', datasets)
  channelTypes.value = datasets.map(ds => {
    const d = camp.datasets[ds]
    const availableFrom = d.available || d.available_from || null
    const isPlanned = !!availableFrom && (new Date(availableFrom) > now())
    // Available if any objects exist in default version and not planned in the future
    const defVer = d.default_version && d.versions ? d.versions[d.default_version] : null
    const hasObjects = !!(defVer && defVer.objects && Object.keys(defVer.objects).length)
    const available = hasObjects && !isPlanned
    return { id: ds, label: ds, available }
  })

  // Objects union across datasets' default versions
  const objectsSet = new Set()
  for (const ds of datasets) {
    const d = camp.datasets[ds]
    const defVer = d.default_version && d.versions ? d.versions[d.default_version] : null
    if (defVer && defVer.objects) {
      console.log('[ColliderML] objects for dataset', ds, 'default_version', d.default_version, ':', Object.keys(defVer.objects))
      Object.keys(defVer.objects).forEach(o => objectsSet.add(o))
    }
  }
  const discoveredObjects = Array.from(objectsSet)
  console.log('[ColliderML] union of objects across datasets:', discoveredObjects)
  objectTypes.value = discoveredObjects.map(o => {
    // Available if at least one dataset has entries for this object and not planned
    let available = false
    for (const ds of datasets) {
      const d = camp.datasets[ds]
      const availableFrom = d.available || d.available_from || null
      const isPlanned = !!availableFrom && (new Date(availableFrom) > now())
      const defVer = d.default_version && d.versions ? d.versions[d.default_version] : null
      if (defVer && defVer.objects && defVer.objects[o] && defVer.objects[o].length && !isPlanned) {
        available = true
        break
      }
    }
    return { id: o, label: o.replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase()), size: objectDisplaySizes[o] || 0, available }
  })
}

onMounted(async () => {
  for (const url of manifestUrlCandidates) {
    try {
      const res = await fetch(url, { cache: 'no-store' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      // Guard against HTML or invalid JSON
      const text = await res.text()
      try {
        manifest.value = JSON.parse(text)
      } catch (parseErr) {
        throw new Error('Manifest is not valid JSON')
      }
      // Pick default campaign from manifest if available
      try {
        const campaigns = manifest.value?.campaigns || {}
        const defaultEntry = Object.entries(campaigns).find(([, v]) => v && v.default)
        const firstKey = Object.keys(campaigns)[0]
        selectedCampaign.value = defaultEntry ? defaultEntry[0] : (firstKey || selectedCampaign.value)
      } catch {}
      deriveFromManifest()
      return
    } catch (e) {
      console.warn('Failed to load manifest from', url, e)
      continue
    }
  }
  // No manifest available; proceed with empty defaults
})

// Add scaling factors for pileup types
const pileupScaling = {
  'pileup-200': 1.0,    // Full size
  'pileup-10': 0.1,     // 10% of full size
  'single_particle': 0.01  // 1% of full size
}

// Base size calculation per channel
const baseChannelSizeGB = computed(() => {
  // This is the size for 100,000 events
  return selections.value.objects.reduce((total, id) => {
    const obj = objectTypes.value.find(o => o.id === id)
    return total + (obj?.size || 0)
  }, 0)
})

// Total size calculation accounting for channels and pileup
const rawSizeGB = computed(() => {
  const channelCount = selections.value.channels.length
  console.log('Channel count:', channelCount)
  if (channelCount === 0) return 0

  // Log base channel size
  console.log('Base channel size (GB per 100,000 events):', baseChannelSizeGB.value)

  // First get size for 1000 events with pileup
  const sizeFor100_000Events = selections.value.pileup.reduce((total, pileupType) => {
    const scaling = pileupScaling[pileupType] || 0
    console.log(`Pileup type: ${pileupType}, scaling: ${scaling}`)
    const size = baseChannelSizeGB.value * channelCount * scaling
    console.log(`Size after pileup scaling: ${size}GB`)
    return total + size
  }, 0)
  console.log('Size for 100,000 events:', sizeFor100_000Events)

  // Then scale down to actual event count
  const finalSize = sizeFor100_000Events * (selections.value.eventCount / 1000)
  console.log(`Event count: ${selections.value.eventCount}`)
  console.log(`Final size after event scaling: ${finalSize}GB`)
  return finalSize
})

// Format size for display
const estimatedSize = computed(() => {
  const sizeGB = rawSizeGB.value
  if (sizeGB >= 1000) {
    return `${(sizeGB / 1000).toFixed(1)}TB`
  } else if (sizeGB < 0.1) {
    return `${(sizeGB * 1000).toFixed(0)}MB`
  } else {
    return `${sizeGB.toFixed(1)}GB`
  }
})

const estimatedTime = computed(() => {
  const speed = 150 // MB/s
  const sizeInMB = rawSizeGB.value * 1024
  const seconds = sizeInMB / speed
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return hours > 0 
    ? `${hours}h ${minutes}m`
    : `${minutes}m`
})

const command = computed(() => {
  let cmd = 'colliderml get'
  // campaign
  if (selectedCampaign.value) {
    cmd += ` -c ${selectedCampaign.value}`
  }
  // datasets
  if (selections.value.channels.length) {
    cmd += ' -d ' + selections.value.channels.join(',')
  }
  // objects
  if (selections.value.objects.length) {
    cmd += ' -o ' + selections.value.objects.join(',')
  }
  // events
  cmd += ` -e ${selections.value.eventCount}`
  // output dir
  cmd += ' -O data'
  return cmd
})

const toggleItem = (category, id) => {
  // Only toggle if the item is available
  const items = selections.value[category]
  const itemList = category === 'channels' ? channelTypes.value : 
                  category === 'pileup' ? pileupTypes :
                  objectTypes.value
  const item = itemList.find(i => i.id === id)
  
  if (!item?.available) return // Don't toggle if not available
  
  const index = items.indexOf(id)
  if (index === -1) {
    items.push(id)
  } else {
    items.splice(index, 1)
  }
}

const selectAll = (category, items) => {
  // Only select available items
  selections.value[category] = items
    .filter(item => item.available)
    .map(item => item.id)
}

const deselectAll = (category) => {
  selections.value[category] = []
}

const isSelected = (category, id) => selections.value[category].includes(id)

const toggleExpand = (category) => {
  expanded.value[category] = !expanded.value[category]
}

const isCopied = ref(false)

const copyCommand = async () => {
  try {
    await navigator.clipboard.writeText(command.value)
    isCopied.value = true
    setTimeout(() => {
      isCopied.value = false
    }, 2000)
  } catch (err) {
    console.warn('Failed to copy:', err)
    // Fallback for older browsers
    const el = document.createElement('textarea')
    el.value = command.value
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
    isCopied.value = true
    setTimeout(() => {
      isCopied.value = false
    }, 2000)
  }
}

// Define discrete event count values (all possible values)
const eventCountValues = [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000]

const maxAvailableEvents = ref(1000)

// Recompute max available events from manifest based on current selections
watchEffect(() => {
  if (!manifest.value) return
  const camp = manifest.value.campaigns?.[selectedCampaign.value]
  if (!camp) return
  const selectedDatasets = selections.value.channels
  const selectedObjects = selections.value.objects
  let total = 0
  console.log('[ColliderML] recomputing maxAvailableEvents for datasets', selectedDatasets, 'objects', selectedObjects)
  for (const ds of selectedDatasets) {
    const d = camp.datasets?.[ds]
    if (!d) continue
    const defVer = d.default_version && d.versions ? d.versions[d.default_version] : null
    if (!defVer || !defVer.objects) continue
    for (const obj of selectedObjects) {
      const segments = defVer.objects[obj] || []
      console.log('[ColliderML] segments for', ds, obj, ':', segments)
      for (const seg of segments) {
        const s = Number(seg.start_event) || 0
        const e = Number(seg.end_event) || 0
        if (e >= s) total += (e - s + 1)
      }
    }
  }
  // Fallback to 1000 if nothing computed
  maxAvailableEvents.value = Math.max(total, 1000)
  // Clamp current selection if needed
  if (selections.value.eventCount > maxAvailableEvents.value) {
    selections.value.eventCount = maxAvailableEvents.value
  }
  console.log('[ColliderML] maxAvailableEvents:', maxAvailableEvents.value)
})

// Helper function to convert between slider index and event count
const logSliderToEvents = (value) => {
  // Only allow selecting up to maxAvailableEvents
  const limitIndex = eventCountValues.findIndex(v => v > maxAvailableEvents.value)
  const cappedIndex = Math.min(value, (limitIndex === -1 ? eventCountValues.length : limitIndex) - 1)
  const selectedValue = eventCountValues[cappedIndex]
  return Math.min(selectedValue, maxAvailableEvents.value)
}

const eventsToLogSlider = (events) => {
  // Find the closest index that doesn't exceed the event count
  const index = eventCountValues.findIndex(v => v >= events)
  return index === -1 ? eventCountValues.length - 1 : index
}

const sliderValue = computed({
  get: () => eventsToLogSlider(selections.value.eventCount),
  set: (value) => {
    // Ensure we don't exceed maxAvailableEvents
    selections.value.eventCount = logSliderToEvents(value)
  }
})

// Format event count for display
const formatEventCount = (count) => {
  if (count >= 1000000) return `${count/1000000}M`
  if (count >= 1000) return `${count/1000}k`
  return count.toString()
}

// Add a computed property for tick classes
const getTickClass = (value) => {
  return {
    active: value <= selections.value.eventCount,
    available: value <= maxAvailableEvents.value,
    inactive: value > maxAvailableEvents.value
  }
}

// Find the index of the max available value
const maxAvailableIndex = eventCountValues.length - 1
</script>

<template>
  <div class="config-modal">
    <div class="config-panel">
      <h3>Dataset Configuration</h3>
      
      <!-- Channels Card -->
      <div class="config-card">
        <div class="card-header">
          <h4>Channels</h4>
          <button class="expand-button" :class="{ expanded: expanded.channels }" @click="toggleExpand('channels')">
            {{ expanded.channels ? '↑ Show Less' : '↓ Show More' }}
          </button>
        </div>
        <div class="button-grid">
          <button
            v-for="channel in channelTypes.filter(c => isSelected('channels', c.id) || expanded.channels)"
            :key="channel.id"
            class="select-button"
            :class="{ 
              selected: isSelected('channels', channel.id),
              inactive: !channel.available 
            }"
            @click="toggleItem('channels', channel.id)"
          >
            {{ channel.label }}
            <span v-if="!channel.available" class="coming-soon">Coming Soon</span>
          </button>
        </div>
        <div v-if="expanded.channels" class="select-all">
          <div class="button-group">
            <button class="select-all-button" @click="deselectAll('channels')">
              Deselect All
            </button>
            <button class="select-all-button" @click="selectAll('channels', channelTypes)">
              Select All
            </button>
          </div>
        </div>
      </div>
      
      <!-- Pile-up Card -->
      <div class="config-card">
        <div class="card-header">
          <h4>Pile-up</h4>
          <button class="expand-button" :class="{ expanded: expanded.pileup }" @click="toggleExpand('pileup')">
            {{ expanded.pileup ? '↑ Show Less' : '↓ Show More' }}
          </button>
        </div>
        <div class="button-grid">
          <button
            v-for="pu in pileupTypes.filter(p => isSelected('pileup', p.id) || expanded.pileup)"
            :key="pu.id"
            class="select-button"
            :class="{ 
              selected: isSelected('pileup', pu.id),
              inactive: !pu.available 
            }"
            @click="toggleItem('pileup', pu.id)"
          >
            {{ pu.label }}
            <span v-if="!pu.available" class="coming-soon">Coming Soon</span>
          </button>
        </div>
        <div v-if="expanded.pileup" class="select-all">
          <div class="button-group">
            <button class="select-all-button" @click="deselectAll('pileup')">
              Deselect All
            </button>
            <button class="select-all-button" @click="selectAll('pileup', pileupTypes)">
              Select All
            </button>
          </div>
        </div>
      </div>
      
      <!-- Objects Card -->
      <div class="config-card">
        <div class="card-header">
          <h4>Objects</h4>
          <button class="expand-button" :class="{ expanded: expanded.objects }" @click="toggleExpand('objects')">
            {{ expanded.objects ? '↑ Show Less' : '↓ Show More' }}
          </button>
        </div>
        <div class="button-grid">
          <button
            v-for="obj in objectTypes.filter(o => isSelected('objects', o.id) || expanded.objects)"
            :key="obj.id"
            class="select-button"
            :class="{ 
              selected: isSelected('objects', obj.id),
              inactive: !obj.available 
            }"
            @click="toggleItem('objects', obj.id)"
          >
            {{ obj.label }}
            <span v-if="!obj.available" class="coming-soon">Coming Soon</span>
          </button>
        </div>
        <div v-if="expanded.objects" class="select-all">
          <div class="button-group">
            <button class="select-all-button" @click="deselectAll('objects')">
              Deselect All
            </button>
            <button class="select-all-button" @click="selectAll('objects', objectTypes)">
              Select All
            </button>
          </div>
        </div>
      </div>

      <!-- Processing and Estimation Card -->
      <div class="config-card">
        <div class="processing-estimation-grid">
          <!-- Processing Section -->
          <div class="processing-section">
            <h4>Processing</h4>
            <div class="processing-options">
              <label class="switch">
                <input type="checkbox" v-model="selections.processing.pytorch">
                <span class="slider"></span>
                <span class="label">PyTorch Ready</span>
              </label>
            </div>
          </div>

          <!-- Estimation Section -->
          <div class="estimation-section">
            <h4>Estimation</h4>
            <div class="estimates">
              <div class="estimate-item">
                <span class="label">Size</span>
                <div class="value-box">{{ estimatedSize }}</div>
              </div>
              <div class="estimate-item">
                <span class="label">Time</span>
                <div class="value-box">~{{ estimatedTime }}</div>
              </div>
              <div class="estimate-item">
                <span class="label">Speed</span>
                <div class="value-box">150MB/s</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Event Count Slider Card -->
      <div class="config-card">
        <div class="card-header">
          <h4>Number of Events</h4>
        </div>
        <div class="slider-container">
          <div class="slider-with-labels">
            <span class="slider-label">100</span>
            <div class="slider-track-container">
              <input 
                type="range" 
                v-model="sliderValue" 
                :min="0" 
                :max="maxAvailableIndex"
                step="1"
                class="range-slider"
              >
              <div class="tick-marks">
                <div 
                  v-for="(value, index) in eventCountValues" 
                  :key="index"
                  class="tick"
                  :class="getTickClass(value)"
                >
                  <span class="tick-label" :class="{ inactive: value > maxAvailableEvents }">
                    {{ formatEventCount(value) }}
                  </span>
                </div>
              </div>
              <div class="coming-soon-label">Coming Soon</div>
            </div>
            <span class="slider-label">1M</span>
          </div>
          <!-- <div class="slider-value">{{ selections.eventCount.toLocaleString() }} events</div> -->
        </div>
      </div>
    </div>
    
    <!-- Command Display -->
    <div class="command-section">
      <div class="command">
        <code>{{ command }}</code>
        <button 
          @click="copyCommand" 
          class="copy-button" 
          :class="{ 'copied': isCopied }"
          :title="isCopied ? 'Copied!' : 'Copy to clipboard'"
        >
          <svg v-if="!isCopied" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </button>
      </div>
    </div>
  </div>
  <p class="footnote">* Particle truth information and event-level information are included by default.</p>
</template>

<style scoped>
.config-modal {
  background: var(--vp-c-bg-soft);
  border-radius: 12px;
  padding: 24px;
  margin: 24px 0;
  box-shadow: var(--modal-shadow);
}

.config-panel {
  background: var(--vp-c-bg);
  border-radius: 8px;
  padding: 20px;
}

.section {
  margin-top: 20px;
}

h3 {
  margin: 0 0 20px 0;
  font-size: 1.2em;
  color: var(--vp-c-text-1);
}

h4 {
  margin: 0 0 12px 0;
  font-size: 1em;
  color: var(--vp-c-text-2);
}

.config-card {
  background: var(--vp-c-bg);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  cursor: pointer;
}

.card-header h4 {
  margin: 0;
}

.expand-button {
  background: none;
  border: none;
  color: var(--vp-c-text-2);
  cursor: pointer;
  font-size: 0.9em;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.expand-button:hover {
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-1);
}

.button-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
  margin-bottom: 8px;
}

.select-button {
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.9em;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 100%;
  text-align: center;
}

.select-button.selected {
  background: var(--vp-c-brand);
  color: white;
  border-color: var(--vp-c-brand);
}

.select-button:hover:not(.selected) {
  border-color: var(--vp-c-brand);
}

.select-all {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.button-group {
  display: flex;
  gap: 8px;
}

.select-all-button {
  background: none;
  border: 1px solid var(--vp-c-divider);
  border-radius: 4px;
  padding: 4px 12px;
  font-size: 0.9em;
  color: var(--vp-c-text-2);
  cursor: pointer;
  transition: all 0.2s ease;
}

.select-all-button:hover {
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-1);
  border-color: var(--vp-c-brand);
}

.processing-estimation-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}

.processing-section, .estimation-section {
  min-width: 0;
}

.processing-section h4, .estimation-section h4 {
  margin-top: 0;
}

.estimates {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.estimate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.estimate-item .label {
  color: var(--vp-c-text-2);
  white-space: nowrap;
}

.value-box {
  background: var(--vp-c-bg-soft);
  padding: 4px 12px;
  border-radius: 6px;
  font-weight: 500;
  min-width: 80px;
  text-align: center;
  white-space: nowrap;
}

.command-section {
  background: var(--vp-c-bg);
  border-radius: 8px;
  padding: 16px;
}

.command {
  display: flex;
  align-items: stretch;
  background: var(--vp-c-bg-soft);
  padding: 0;
  border-radius: 6px;
  overflow: hidden;
}

.command code {
  padding: 12px;
  flex-grow: 1;
}

.copy-button {
  background: transparent;
  color: var(--vp-c-text-2);
  border: none;
  border-left: 1px solid var(--vp-c-divider);
  padding: 0 12px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
}

.copy-button:hover {
  background: var(--vp-c-bg-mute);
  color: var(--vp-c-text-1);
}

.copy-button.copied {
  color: var(--vp-c-green);
  background: var(--vp-c-bg-mute);
}

.processing-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.switch {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  position: relative;
}

.switch input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: relative;
  width: 36px;
  height: 20px;
  background: var(--vp-c-bg-soft);
  border-radius: 10px;
  transition: 0.3s;
}

.slider:before {
  content: "";
  position: absolute;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  top: 2px;
  left: 2px;
  transition: 0.3s;
}

input:checked + .slider {
  background: var(--vp-c-brand);
}

input:checked + .slider:before {
  transform: translateX(16px);
}

.switch .label {
  color: var(--vp-c-text-1);
  font-size: 0.9em;
}

/* Updated Slider styles */
.slider-container {
  padding: 1rem;
}

.slider-with-labels {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.slider-track-container {
  flex-grow: 1;
  position: relative;
  padding: 1rem 0;
}

.tick-marks {
  position: absolute;
  left: 0;
  right: 0;
  bottom: -4px;
  display: flex;
  justify-content: space-between;
  pointer-events: none;
}

.tick {
  position: relative;
  width: 2px;
  height: 8px;
  background: var(--vp-c-divider);
  transition: background-color 0.2s;
}

.tick.active {
  background: var(--vp-c-brand);
}

.tick.inactive {
  opacity: 0.5;
}

.tick-label {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%) rotate(-45deg);
  font-size: 0.8em;
  color: var(--vp-c-text-2);
  white-space: nowrap;
}

.tick-label.inactive {
  opacity: 0.5;
  font-style: italic;
}

.range-slider {
  -webkit-appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: var(--vp-c-bg-soft);
  outline: none;
  margin: 0;
}

.range-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--vp-c-brand);
  cursor: pointer;
  border: 2px solid var(--vp-c-bg);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: background-color 0.2s, transform 0.1s;
}

.range-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--vp-c-brand);
  cursor: pointer;
  border: 2px solid var(--vp-c-bg);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: background-color 0.2s, transform 0.1s;
}

.range-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.range-slider::-moz-range-thumb:hover {
  transform: scale(1.1);
}

.slider-value {
  text-align: center;
  font-weight: 500;
  color: var(--vp-c-text-1);
  font-size: 1.1em;
  margin-top: 1rem;
}

.select-button.inactive {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--vp-c-bg-mute);
  border-color: var(--vp-c-divider);
  position: relative;
}

.select-button.inactive:hover {
  border-color: var(--vp-c-divider);
}

.coming-soon {
  font-size: 0.7em;
  display: block;
  color: var(--vp-c-text-3);
  margin-top: 0px;
}

.coming-soon-label {
  position: absolute;
  width: 100%;
  text-align: center;
  color: var(--vp-c-text-3);
  font-size: 0.8em;
  font-style: italic;
  margin-top: 3.0rem;
  opacity: 0.7;
}
</style> 