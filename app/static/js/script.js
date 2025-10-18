document.addEventListener('DOMContentLoaded', function() {
    // Инициализация графиков
    let rigModelsChart, efficiencyChart;
    let blocksData = []; // Для хранения данных о блоках
    let remainingShiftsData = []; // Для хранения данных о сменах
    let efficiencyData = []; // Для хранения данных об эффективности
    
    // Загрузка данных
    loadData();
    
    // Поиск блока
    document.getElementById('search-btn').addEventListener('click', searchBlock);
    document.getElementById('block-search').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') searchBlock();
    });
    
    // Закрытие модального окна
    document.querySelector('.close-btn').addEventListener('click', function() {
        document.getElementById('block-modal').style.display = 'none';
    });
    
    // Закрытие модального окна при клике вне его
    window.addEventListener('click', function(event) {
        if (event.target === document.getElementById('block-modal')) {
            document.getElementById('block-modal').style.display = 'none';
        }
    });
    
    // Функция загрузки данных
    async function loadData() {
        try {
            // Загрузка общей статистики
            const blocksProgress = await fetch('/api/blocks/progress').then(res => res.json());
            updateBlocksProgress(blocksProgress);
            
            // Загрузка прогресса по блокам
            const drillingProgress = await fetch('/api/blocks/drilling_progress').then(res => res.json());
            blocksData = drillingProgress;
            
            // Загрузка оставшихся смен
            const shiftsResponse = await fetch('/api/blocks/remaining_shifts').then(res => res.json());
            remainingShiftsData = shiftsResponse;
            
            // Загрузка эффективности бурения
            const efficiencyResponse = await fetch('/api/blocks/efficiency').then(res => res.json());
            efficiencyData = efficiencyResponse;
            
            updateBlocksTable(blocksData);
            
            // Загрузка производительности моделей станков
            const rigModels = await fetch('/api/rigs/models').then(res => res.json());
            initRigModelsChart(rigModels);
            
            // Загрузка эффективности бурения по блокам
            initEfficiencyChart(efficiencyData);
            
        } catch (error) {
            console.error('Ошибка загрузки данных:', error);
            alert('Произошла ошибка при загрузке данных');
        }
    }
    
    // Обновление статистики по блокам
    function updateBlocksProgress(data) {
        document.getElementById('total-blocks').textContent = data.total_blocks;
        document.getElementById('drilled-blocks').textContent = data.drilled_blocks;
        document.getElementById('blocks-progress-value').textContent = data.percent_drilled + '%';
        document.getElementById('blocks-progress-fill').style.width = data.percent_drilled + '%';
    }
    
    // Обновление таблицы блоков
    function updateBlocksTable(data) {
        const tbody = document.querySelector('#blocks-table tbody');
        tbody.innerHTML = '';
        
        data.forEach(block => {
            const row = document.createElement('tr');
            
            // Находим данные о сменах и эффективности для текущего блока
            const shiftsInfo = remainingShiftsData.find(item => item.block_id === block.block_id);
            const efficiencyInfo = efficiencyData.find(item => item.block_id === block.block_id);
            
            row.innerHTML = `
                <td>${block.block_id}</td>
                <td>${block.block_name || '-'}</td>
                <td>${block.total_holes_actual}</td>
                <td>${block.drilled_holes_actual}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${block.percent_drilled_actual}%"></div>
                    </div>
                    <span>${block.percent_drilled_actual}%</span>
                </td>
                <td>${shiftsInfo ? shiftsInfo.remaining_shifts : '-'}</td>
                <td>${efficiencyInfo ? efficiencyInfo.efficiency_percent.toFixed(2) : '-'}%</td>
            `;
            
            // Добавляем обработчик клика для просмотра деталей
            row.addEventListener('click', function() {
                showBlockDetails(block.block_id);
            });
            
            row.style.cursor = 'pointer';
            tbody.appendChild(row);
        });
    }
    
    // Инициализация графика производительности моделей станков
    function initRigModelsChart(data) {
        const ctx = document.getElementById('rigModelsChart').getContext('2d');
        
        if (rigModelsChart) {
            rigModelsChart.destroy();
        }
        
        rigModelsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => item.rig_model),
                datasets: [{
                    label: 'Средняя производительность (м/смену)',
                    data: data.map(item => item.avg_performance_m_per_shift),
                    backgroundColor: data.map((_, i) => 
                        `hsl(${i * 360 / data.length}, 70%, 60%)`),
                    borderColor: data.map((_, i) => 
                        `hsl(${i * 360 / data.length}, 70%, 40%)`),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Метры за смену'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const index = context.dataIndex;
                                return `Количество станков: ${data[index].rig_count}`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Инициализация графика эффективности бурения
    function initEfficiencyChart(data) {
        const ctx = document.getElementById('efficiencyChart').getContext('2d');
        
        if (efficiencyChart) {
            efficiencyChart.destroy();
        }
        
        // Сортируем данные по эффективности
        data.sort((a, b) => b.efficiency_percent - a.efficiency_percent);
        
        // Берем топ-10 блоков
        // const topData = data.slice(0, 10);
        const topData = data;
        
        efficiencyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: topData.map(item => item.block_id),
                datasets: [{
                    label: 'Эффективность бурения (%)',
                    data: topData.map(item => item.efficiency_percent),
                    backgroundColor: topData.map((_, i) => 
                        `hsl(${120 + i * 30}, 70%, 60%)`),
                    borderColor: topData.map((_, i) => 
                        `hsl(${120 + i * 30}, 70%, 40%)`),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Процент полезного времени'
                        }
                    }
                }
            }
        });
    }
    
    // Поиск блока
    async function searchBlock() {
        const blockId = document.getElementById('block-search').value.trim();
        if (!blockId) {
            alert('Введите ID блока для поиска');
            return;
        }
        
        try {
            const response = await fetch(`/api/block/search?id=${blockId}`);
            if (!response.ok) {
                throw new Error('Блок не найден');
            }
            const data = await response.json();
            showBlockDetails(blockId, data);
        } catch (error) {
            alert(error.message);
        }
    }
    
    // Показать детали блока
    function showBlockDetails(blockId, data = null) {
        const modal = document.getElementById('block-modal');
        
        if (data) {
            // Если данные уже получены (при поиске)
            updateModalContent(data);
            modal.style.display = 'block';
        } else {
            // Загружаем данные при клике на строку таблицы
            fetch(`/api/block/search?id=${blockId}`)
                .then(response => {
                    if (!response.ok) throw new Error('Блок не найден');
                    return response.json();
                })
                .then(data => {
                    updateModalContent(data);
                    modal.style.display = 'block';
                })
                .catch(error => {
                    alert(error.message);
                });
        }
    }
    
    // Обновление содержимого модального окна
    function updateModalContent(data) {
        const block = data.block;
        
        document.getElementById('modal-title').textContent = `Детали блока: ${block.block_id}`;
        document.getElementById('block-id').textContent = block.block_id;
        document.getElementById('block-name').textContent = block.block_name || '-';
        document.getElementById('block-progress-value').textContent = block.percent_drilled_actual + '%';
        document.getElementById('block-progress-fill').style.width = block.percent_drilled_actual + '%';
        document.getElementById('remaining-shifts').textContent = data.remaining_shifts || '-';
        document.getElementById('efficiency').textContent = (data.efficiency ? data.efficiency : '0') + '%';
        
        // Заполняем таблицу станков
        const tbody = document.querySelector('#rigs-table tbody');
        tbody.innerHTML = '';
        
        if (data.rigs && data.rigs.length > 0) {
            data.rigs.forEach(rig => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${rig.rig_id || '-'}</td>
                    <td>${rig.rig_name || '-'}</td>
                    <td>${rig.rig_model || '-'}</td>
                    <td>${rig.total_depth || '-'}</td>
                    <td>${rig.drill_hours || '-'}</td>
                    <td>${rig.shifts_count || '-'}</td>
                    <td>${rig.remaining_depth || '-'}</td>
                    <td>${rig.remaining_shifts || '-'}</td>
                    <td>${rig.performance_m_per_shift || '-'}</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="7" style="text-align: center;">Нет данных о станках</td>';
            tbody.appendChild(row);
        }
    }
});