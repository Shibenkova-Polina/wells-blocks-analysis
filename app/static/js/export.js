// static/js/export.js

// Функция для экспорта отчетов
function exportReport(reportType, format) {
    const url = `/api/export/${reportType}/${format}`;
    
    // Показать индикатор загрузки
    showLoadingIndicator();
    
    // Скачать файл
    const link = document.createElement('a');
    link.href = url;
    link.download = '';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Скрыть индикатор загрузки
    hideLoadingIndicator();
}

// Функция для экспорта отчета по блоку
function exportBlockReport(format) {
    const blockId = '{{ block_id }}';
    const url = `/api/export/block_${blockId}/${format}`;
    
    showLoadingIndicator();
    
    const link = document.createElement('a');
    link.href = url;
    link.download = '';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    hideLoadingIndicator();
}

// Функции для индикатора загрузки
function showLoadingIndicator() {
    let loader = document.getElementById('export-loader');
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'export-loader';
        loader.innerHTML = '<div class="loading-spinner">Подготовка файла...</div>';
        loader.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
        `;
        document.body.appendChild(loader);
    }
}

function hideLoadingIndicator() {
    const loader = document.getElementById('export-loader');
    if (loader) {
        loader.remove();
    }
}

// Обработчик ошибок
function handleExportError(error) {
    console.error('Export error:', error);
    alert('Произошла ошибка при экспорте отчета. Пожалуйста, попробуйте еще раз.');
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем стили для кнопок экспорта
    const style = document.createElement('style');
    style.textContent = `
        .export-options {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .export-section {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }
        
        .export-section h3 {
            margin-top: 0;
            color: #495057;
            font-size: 16px;
        }
        
        .export-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .btn-export {
            background: #28a745;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .btn-export:hover {
            background: #218838;
        }
        
        .export-dropdown {
            position: relative;
            display: inline-block;
        }
        
        .export-dropdown-content {
            display: none;
            position: absolute;
            background-color: white;
            min-width: 160px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            z-index: 1;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .export-dropdown-content a {
            color: #333;
            padding: 8px 12px;
            text-decoration: none;
            display: block;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .export-dropdown-content a:hover {
            background-color: #f8f9fa;
        }
        
        .export-dropdown:hover .export-dropdown-content {
            display: block;
        }
        
        .loading-spinner {
            text-align: center;
            color: #495057;
        }
    `;
    document.head.appendChild(style);
});