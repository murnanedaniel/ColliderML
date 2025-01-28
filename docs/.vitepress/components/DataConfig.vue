<script setup>
import { ref, computed } from 'vue'

const selections = ref({
  objects: ['tracks', 'calo_clusters'],
  processing: {
    merge: false,
    pytorch: false
  }
})

// size in GB
const objectTypes = [
{ id: 'partons', label: 'Partons', size: 100 },
{ id: 'tracker_hits', label: 'Tracker Hits', size: 1000 },  
{ id: 'calo_hits', label: 'Calo Hits', size: 3000 },
{ id: 'tracks', label: 'Tracks', size: 10 }, 
{ id: 'jets', label: 'Jets', size: 5 },
{ id: 'calo_clusters', label: 'Calo Clusters', size: 100 },
{ id: 'particle_flow_objects', label: 'Particle Flow Objects', size: 20 },
]

const rawSizeGB = computed(() => {
  return selections.value.objects.reduce((total, id) => {
    const obj = objectTypes.find(o => o.id === id)
    return total + (obj?.size || 0)
  }, 0)
})

const estimatedSize = computed(() => {
  return rawSizeGB.value >= 1000 
    ? `${(rawSizeGB.value / 1000).toFixed(1)}TB`
    : `${rawSizeGB.value}GB`
})

const estimatedTime = computed(() => {
  const speed = 150 // MB/s
  const sizeInMB = rawSizeGB.value * 1024
  const seconds = sizeInMB / speed
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}h ${minutes}m`
})

const command = computed(() => {
  let cmd = 'colliderml download'
  
  // Add object selections
  if (selections.value.objects.length) {
    cmd += ' --objects ' + selections.value.objects.join(',')
  }
  
  // Add processing options
  if (selections.value.processing.merge) cmd += ' --merge'
  if (selections.value.processing.pytorch) cmd += ' --pytorch'
  
  return cmd
})

const toggleObject = (id) => {
  const index = selections.value.objects.indexOf(id)
  if (index === -1) {
    selections.value.objects.push(id)
  } else {
    selections.value.objects.splice(index, 1)
  }
}

const isSelected = (id) => selections.value.objects.includes(id)

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
</script>

<template>
  <div class="config-modal">
    <div class="config-grid">
      <!-- Configuration Panel -->
      <div class="config-panel">
        <h3>Dataset Configuration</h3>
        
        <div class="section">
          <h4>Include*</h4>
          <div class="object-buttons">
            <button
              v-for="obj in objectTypes"
              :key="obj.id"
              class="object-button"
              :class="{ selected: isSelected(obj.id) }"
              @click="toggleObject(obj.id)"
            >
              {{ obj.label }}
            </button>
          </div>
        </div>
        
        <div class="section">
          <h4>Processing</h4>
          <div class="processing-options">
            <label class="switch">
              <input type="checkbox" v-model="selections.processing.merge">
              <span class="slider"></span>
              <span class="label">Merge Objects</span>
            </label>
            <label class="switch">
              <input type="checkbox" v-model="selections.processing.pytorch">
              <span class="slider"></span>
              <span class="label">PyTorch Ready</span>
            </label>
          </div>
        </div>
      </div>
      
      <!-- Estimation Panel -->
      <div class="estimation-panel">
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

.config-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.config-panel, .estimation-panel {
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

.object-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.object-button {
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 20px;
  padding: 6px 16px;
  font-size: 0.9em;
  cursor: pointer;
  transition: all 0.2s ease;
}

.object-button.selected {
  background: var(--vp-c-brand);
  color: white;
  border-color: var(--vp-c-brand);
}

.object-button:hover {
  border-color: var(--vp-c-brand);
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

.estimates {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.estimate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.estimate-item .label {
  color: var(--vp-c-text-2);
}

.estimate-item .value {
  font-weight: 500;
}

.value-box {
  background: var(--vp-c-bg-soft);
  padding: 4px 12px;
  border-radius: 6px;
  font-weight: 500;
  min-width: 80px;
  text-align: center;
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
</style> 