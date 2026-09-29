// ==========================================================================
// Chart.js Visualizations for Personal Finance Advisor Bot
// ==========================================================================

const FinanceCharts = {
    categoryColors: [
        '#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#06b6d4',
        '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#64748b'
    ],

    renderCategoryDoughnut(canvasId, labels, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (!data || data.length === 0 || data.every(v => v === 0)) {
            // Display empty notice on canvas container
            const container = ctx.parentElement;
            container.innerHTML = `
                <div class="empty-state" style="padding: 2rem 1rem;">
                    <div class="empty-state-icon" style="width: 48px; height: 48px; font-size: 1.25rem;">
                        <i class="fa-solid fa-chart-pie"></i>
                    </div>
                    <p class="empty-state-desc">No expense records found for this period.</p>
                </div>
            `;
            return null;
        }

        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: this.categoryColors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: '#ffffff',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            padding: 14,
                            font: { family: 'Inter', size: 12 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const val = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                return ` ${context.label}: ₹${val.toLocaleString('en-IN')} (${pct}%)`;
                            }
                        }
                    }
                },
                cutout: '68%'
            }
        });
    },

    renderIncomeExpenseBar(canvasId, labels, incomeData, expenseData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Income',
                        data: incomeData,
                        backgroundColor: '#10b981',
                        borderRadius: 6,
                        maxBarThickness: 28
                    },
                    {
                        label: 'Expenses',
                        data: expenseData,
                        backgroundColor: '#ef4444',
                        borderRadius: 6,
                        maxBarThickness: 28
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end',
                        labels: {
                            boxWidth: 12,
                            padding: 10,
                            font: { family: 'Inter', size: 12 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` ${context.dataset.label}: ₹${Number(context.raw || 0).toLocaleString('en-IN')}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#f1f5f9' },
                        ticks: {
                            callback: function(val) {
                                if (val >= 1000) return '₹' + (val / 1000) + 'k';
                                return '₹' + val;
                            },
                            font: { family: 'Inter', size: 11 }
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: 'Inter', size: 11 } }
                    }
                }
            }
        });
    },

    renderSavingsTrendLine(canvasId, labels, savingsData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Net Monthly Savings',
                    data: savingsData,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.35,
                    fill: true,
                    pointBackgroundColor: '#4f46e5',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` Net Savings: ₹${Number(context.raw || 0).toLocaleString('en-IN')}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        grid: { color: '#f1f5f9' },
                        ticks: {
                            callback: function(val) {
                                if (Math.abs(val) >= 1000) return '₹' + (val / 1000) + 'k';
                                return '₹' + val;
                            },
                            font: { family: 'Inter', size: 11 }
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: 'Inter', size: 11 } }
                    }
                }
            }
        });
    }
};
