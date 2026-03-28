<template>
  <div class="d-inline-block">
    <!-- Idle -->
    <button v-if="state === 'idle'"
            class="btn btn-sm btn-outline-secondary"
            @click="startExport">
      Export CSV
    </button>

    <!-- Polling -->
    <button v-else-if="state === 'polling'"
            class="btn btn-sm btn-outline-secondary" disabled>
      <span class="spinner-border spinner-border-sm me-1"></span>
      Generating…
    </button>

    <!-- Done -->
    <a v-else-if="state === 'done'"
       :href="downloadUrl"
       class="btn btn-sm btn-success"
       target="_blank"
       @click="reset">
      Download CSV
    </a>

    <!-- Error -->
    <button v-else-if="state === 'error'"
            class="btn btn-sm btn-outline-danger"
            @click="reset">
      Export failed — retry
    </button>

    <!-- Status text -->
    <span v-if="statusText"
          class="text-muted small ms-2">{{ statusText }}</span>
  </div>
</template>

<script>
import api from '../api'

export default {
  name: 'ExportButton',
  props: {
    /** 'student' | 'company' */
    role: { type: String, required: true },
  },
  data() {
    return {
      state:       'idle',   // idle | polling | done | error
      taskId:      null,
      downloadUrl: null,
      statusText:  '',
      pollTimer:   null,
    }
  },
  beforeUnmount() {
    clearInterval(this.pollTimer)
  },
  methods: {
    async startExport() {
      this.state      = 'polling'
      this.statusText = 'Starting export job…'
      try {
        const endpoint = this.role === 'student'
          ? '/jobs/export/student'
          : '/jobs/export/company'
        const { data } = await api.post(endpoint)
        this.taskId    = data.task_id
        this.statusText = 'Job queued — polling for result…'
        this.pollTimer  = setInterval(this.pollStatus, 2500)
      } catch (err) {
        this.state      = 'error'
        this.statusText = err.response?.data?.message || 'Failed to start export.'
      }
    },

    async pollStatus() {
      if (!this.taskId) return
      try {
        const { data } = await api.get(`/jobs/status/${this.taskId}`)

        if (data.status === 'SUCCESS') {
          clearInterval(this.pollTimer)
          this.downloadUrl = data.result?.download_url
          this.state       = 'done'
          this.statusText  = `${data.result?.total_rows ?? ''} rows ready`
        } else if (data.status === 'FAILURE') {
          clearInterval(this.pollTimer)
          this.state      = 'error'
          this.statusText = data.error || 'Export failed.'
        } else {
          this.statusText = `Status: ${data.status}…`
        }
      } catch {
        clearInterval(this.pollTimer)
        this.state      = 'error'
        this.statusText = 'Could not reach server.'
      }
    },

    reset() {
      clearInterval(this.pollTimer)
      this.state       = 'idle'
      this.taskId      = null
      this.downloadUrl = null
      this.statusText  = ''
    },
  },
}
</script>
