<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">Background Jobs</h5>

    <div class="row g-4">

      <!-- Interview Reminders -->
      <div class="col-md-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white fw-semibold">
            Interview Reminder Job
          </div>
          <div class="card-body">
            <p class="text-muted small mb-3">
              Sends email reminders to all students with interviews
              scheduled in the next 24 hours. Runs automatically
              daily at 08:00 IST via Celery Beat.
            </p>
            <div class="d-flex align-items-center gap-3">
              <button class="btn btn-primary btn-sm"
                      :disabled="reminderState === 'polling'"
                      @click="trigger('reminders/trigger', 'reminderState', 'reminderResult')">
                <span v-if="reminderState === 'polling'"
                      class="spinner-border spinner-border-sm me-1"></span>
                Run Now
              </button>
              <span v-if="reminderResult"
                    class="small text-success">
                {{ reminderResult }}
              </span>
            </div>
          </div>
          <div class="card-footer bg-transparent small text-muted">
            Schedule: daily 08:00 IST · Channel: Email + GChat
          </div>
        </div>
      </div>

      <!-- Monthly Report -->
      <div class="col-md-6">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-header bg-white fw-semibold">
            Monthly Placement Report
          </div>
          <div class="card-body">
            <p class="text-muted small mb-3">
              Generates an HTML activity report for the previous month
              (drives, applications, placements, analytics) and emails
              it to the admin. Runs automatically on the 1st of each month.
            </p>
            <div class="d-flex align-items-center gap-3 flex-wrap">
              <button class="btn btn-primary btn-sm"
                      :disabled="reportState === 'polling'"
                      @click="trigger('report/trigger', 'reportState', 'reportResult')">
                <span v-if="reportState === 'polling'"
                      class="spinner-border spinner-border-sm me-1"></span>
                Generate Now
              </button>
              <a v-if="reportDownload"
                 :href="reportDownload"
                 target="_blank"
                 class="btn btn-sm btn-outline-success">
                Download Report
              </a>
              <span v-if="reportResult"
                    class="small text-success">{{ reportResult }}</span>
            </div>
          </div>
          <div class="card-footer bg-transparent small text-muted">
            Schedule: 1st of month 07:00 IST · Sent to admin email
          </div>
        </div>
      </div>

      <!-- Job status log -->
      <div class="col-12" v-if="log.length">
        <div class="card border-0 shadow-sm">
          <div class="card-header bg-white fw-semibold
                      d-flex justify-content-between align-items-center">
            Job Log
            <button class="btn btn-sm btn-outline-secondary"
                    @click="log = []">Clear</button>
          </div>
          <div class="card-body p-0">
            <ul class="list-group list-group-flush">
              <li v-for="(entry, i) in log" :key="i"
                  class="list-group-item py-2 small">
                <div class="d-flex justify-content-between">
                  <div>
                    <span class="badge me-2"
                          :class="entry.status === 'SUCCESS'
                            ? 'bg-success'
                            : entry.status === 'FAILURE'
                              ? 'bg-danger'
                              : 'bg-secondary'">
                      {{ entry.status }}
                    </span>
                    {{ entry.job }}
                    <span v-if="entry.detail" class="text-muted ms-2">
                      · {{ entry.detail }}
                    </span>
                  </div>
                  <span class="text-muted">{{ entry.time }}</span>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import api from '../../api'

export default {
  name: 'AdminJobsView',
  data() {
    return {
      reminderState:  'idle',
      reminderResult: '',
      reportState:    'idle',
      reportResult:   '',
      reportDownload: null,
      log:            [],
      pollTimers:     {},
    }
  },
  beforeUnmount() {
    Object.values(this.pollTimers).forEach(clearInterval)
  },
  methods: {
    async trigger(endpoint, stateKey, resultKey) {
      this[stateKey] = 'polling'
      this[resultKey] = ''
      const jobName = endpoint.includes('reminder') ? 'Interview Reminders' : 'Monthly Report'

      try {
        const { data } = await api.post(`/jobs/${endpoint}`)
        const taskId   = data.task_id

        this.pollTimers[taskId] = setInterval(async () => {
          try {
            const { data: res } = await api.get(`/jobs/status/${taskId}`)

            if (res.status === 'SUCCESS') {
              clearInterval(this.pollTimers[taskId])
              this[stateKey]  = 'done'
              const r         = res.result || {}
              this[resultKey] = r.sent !== undefined
                ? `Sent ${r.sent} reminders`
                : r.filename
                  ? `Report: ${r.filename} · ${r.total_placed} placed`
                  : 'Done'

              if (r.filename) {
                this.reportDownload = `/api/jobs/download/${r.filename}`
              }

              this.log.unshift({
                job:    jobName,
                status: 'SUCCESS',
                detail: this[resultKey],
                time:   new Date().toLocaleTimeString('en-IN'),
              })

            } else if (res.status === 'FAILURE') {
              clearInterval(this.pollTimers[taskId])
              this[stateKey]  = 'error'
              this[resultKey] = res.error || 'Job failed'
              this.log.unshift({
                job:    jobName,
                status: 'FAILURE',
                detail: res.error,
                time:   new Date().toLocaleTimeString('en-IN'),
              })
            }
          } catch {
            clearInterval(this.pollTimers[taskId])
            this[stateKey] = 'error'
          }
        }, 2500)

      } catch (err) {
        this[stateKey]  = 'error'
        this[resultKey] = err.response?.data?.message || 'Failed to start job.'
        this.log.unshift({
          job:    jobName,
          status: 'FAILURE',
          detail: this[resultKey],
          time:   new Date().toLocaleTimeString('en-IN'),
        })
      }
    },
  },
}
</script>
