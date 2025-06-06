let currentImageData = null;
let processedImageBlob = null;

// 页面加载完成后初始化
$(document).ready(function() {
    initializeEventListeners();
    initializeAnimations();
    showWelcomeMessage();
});

// 初始化事件监听器
function initializeEventListeners() {
    // 粘贴事件 - 支持从剪贴板粘贴图片
    $(document).on('paste', function(e) {
        const items = e.originalEvent.clipboardData.items;
        for (let item of items) {
            if (item.type.indexOf('image') !== -1) {
                const file = item.getAsFile();
                handleImageFile(file);
                showToast('已从剪贴板粘贴图片', 'success');
                break;
            }
        }
    });

    // 点击上传区域触发文件选择
    $('#pasteArea').click(function() {
        $('#fileInput').click();
    });

    // 文件选择事件
    $('#fileInput').change(function(e) {
        const file = e.target.files[0];
        if (file) {
            handleImageFile(file);
        }
    });

    // 拖拽事件处理
    $('#pasteArea').on('dragover', function(e) {
        e.preventDefault();
        $(this).addClass('dragover');
    });

    $('#pasteArea').on('dragleave', function(e) {
        e.preventDefault();
        $(this).removeClass('dragover');
    });

    $('#pasteArea').on('drop', function(e) {
        e.preventDefault();
        $(this).removeClass('dragover');
        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith('image/')) {
            handleImageFile(files[0]);
            showToast('已拖拽上传图片', 'success');
        } else {
            showError('请拖拽有效的图片文件');
        }
    });

    // 键盘快捷键
    $(document).keydown(function(e) {
        // Ctrl+R 或 Cmd+R 重置
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            resetTool();
            return;
        }
        
        // ESC键关闭模态框
        if (e.key === 'Escape') {
            $('.modal').modal('hide');
            return;
        }
    });

    // 图片预览点击放大
    $(document).on('click', '.image-preview', function() {
        const src = $(this).attr('src');
        if (src) {
            showImageModal(src);
        }
    });


}

// 初始化页面动画
function initializeAnimations() {
    // 页面加载动画
    $('body').addClass('fade-in');
    
    // 滚动到可见区域时触发动画
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                $(entry.target).addClass('slide-in');
            }
        });
    });

    // 观察需要动画的元素
    $('.main-card').each(function() {
        observer.observe(this);
    });
}

// 显示欢迎消息
function showWelcomeMessage() {
    setTimeout(() => {
        showToast('欢迎使用 DocuScan！选择图片即可自动开始处理', 'info', 4000);
    }, 1000);
}

// 更新处理占位符文本和进度
function updateProcessingProgress() {
    const steps = [
        { text: 'AI正在分析图片...', detail: '分析图像结构和内容', progress: 20 },
        { text: '正在优化画质...', detail: '调整亮度和对比度', progress: 40 },
        { text: '正在增强细节...', detail: '锐化和降噪处理', progress: 60 },
        { text: '正在优化色彩...', detail: '色彩平衡和饱和度', progress: 80 },
        { text: '即将完成处理...', detail: '最终优化和压缩', progress: 95 }
    ];
    
    let stepIndex = 0;
    const interval = setInterval(() => {
        if ($('#processingPlaceholder').is(':visible') && stepIndex < steps.length) {
            const step = steps[stepIndex];
            $('#processingPlaceholder p').text(step.text);
            $('#processingStep').text(step.detail);
            $('#processingProgress').css('width', step.progress + '%');
            stepIndex++;
        } else {
            clearInterval(interval);
        }
    }, 1500);
}

// 处理图片文件
function handleImageFile(file) {
    // 验证文件类型
    if (!file.type.startsWith('image/')) {
        showError('请选择有效的图片文件');
        return;
    }

    // 验证文件大小 (限制为10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showError(`图片文件过大：${formatFileSize(file.size)}，请选择小于10MB的图片`);
        return;
    }

    // 显示加载状态
    showImageLoadingState();

    const reader = new FileReader();
    reader.onload = function(e) {
        currentImageData = e.target.result;
        
        // 隐藏所有提示
        hideAlerts();
        
        // 显示原始图片并开始处理
        showOriginalImage(file);
        processImage();
    };
    
    reader.onerror = function() {
        showError('读取图片文件时发生错误，请重试');
        hideImageLoadingState();
    };
    
    reader.readAsDataURL(file);
}

// 显示图片加载状态
function showImageLoadingState() {
    $('#pasteArea').addClass('loading-state');
    $('#pasteArea .upload-icon').html('⏳');
    $('#pasteArea h4').text('正在加载图片...');
}

// 隐藏图片加载状态
function hideImageLoadingState() {
    $('#pasteArea').removeClass('loading-state');
    $('#pasteArea .upload-icon').html('📸');
    $('#pasteArea h4').text('选择图片开始处理');
}

// 显示原始图片
function showOriginalImage(file) {
    // 隐藏上传区域，显示原始图片容器
    $('#pasteArea').hide();
    $('#originalImageContainer').show();
    
    // 设置原始图片
    $('#originalImage').attr('src', currentImageData);
    
    // 显示图片信息
    const fileSize = formatFileSize(file.size);
    const imageFormat = getImageFormat(file.type);
    $('#imageInfo small').text(`${file.name} • ${fileSize} • ${imageFormat}`);
    
    hideImageLoadingState();
}

// 选择新图片
function selectNewImage() {
    $('#fileInput').click();
}



// 处理图片
function processImage() {
    if (!currentImageData) {
        showError('请先选择或粘贴图片');
        return;
    }

    // 隐藏无图片占位符，显示处理状态
    $('#noImagePlaceholder').hide();
    $('#processingContainer').show();
    showProcessingState();

    // 发送请求
    $.ajax({
        url: '/process-image',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            img: currentImageData
        }),
        xhrFields: {
            responseType: 'blob'
        },
        timeout: 60000, // 60秒超时
        success: function(data, status, xhr) {
            processedImageBlob = data;
            const imageUrl = URL.createObjectURL(data);
            
            // 完成进度条
            $('#processingProgress').css('width', '100%');
            $('#processingStep').text('处理完成！');
            
            // 短暂延迟后隐藏处理容器，显示处理后的图片
            setTimeout(() => {
                $('#processingContainer').fadeOut(300, function() {
                    $('#processedImage').attr('src', imageUrl);
                    $('#processedImageContainer').show().addClass('fade-in processing-complete');
                    
                    // 添加处理完成的视觉提示
                    showProcessingSuccess();
                    
                    // 显示成功消息
                    setTimeout(() => {
                        showSuccess('🎉 图片处理完成！');
                    }, 300);
                });
            }, 800);
        },
        error: function(xhr, status, error) {
            // 隐藏处理容器，显示无图片占位符
            $('#processingContainer').hide();
            $('#processedImageContainer').hide();
            $('#noImagePlaceholder').show();
            
            handleProcessingError(xhr, status, error);
        },
        complete: function() {
            hideProcessingState();
        }
    });
}

// 显示处理状态
function showProcessingState() {
    // 重置处理进度
    $('#processingProgress').css('width', '0%');
    $('#processingStep').text('正在初始化...');
    
    // 开始更新处理进度
    updateProcessingProgress();
    
    // 隐藏错误信息
    hideAlerts();
}

// 隐藏处理状态
function hideProcessingState() {
    hideImageLoadingState();
}

// 处理错误
function handleProcessingError(xhr, status, error) {
    let errorMsg = '处理图片时发生错误';
    
    if (status === 'timeout') {
        errorMsg = '⏰ 请求超时，图片可能过大或网络较慢，请重试';
    } else if (xhr.status === 413) {
        errorMsg = '📏 图片文件太大，请选择较小的图片（建议小于5MB）';
    } else if (xhr.status === 400) {
        try {
            const response = JSON.parse(xhr.responseText);
            errorMsg = response.detail || errorMsg;
        } catch (e) {
            errorMsg = '❌ 图片格式不支持或文件损坏';
        }
    } else if (xhr.status === 0) {
        errorMsg = '🌐 网络连接错误，请检查网络后重试';
    } else if (xhr.status >= 500) {
        errorMsg = '🔧 服务器暂时不可用，请稍后重试';
    }
    
    showError(errorMsg);
}

// 显示处理成功的视觉反馈
function showProcessingSuccess() {
    // 添加成功状态标识
    $('#processedImageContainer').addClass('processing-success');
    
    // 添加成功图标动画
    const successIcon = $('<div class="success-badge">✓</div>');
    $('#processedImageContainer').append(successIcon);
    
    // 移除成功状态
    setTimeout(() => {
        $('#processedImageContainer').removeClass('processing-success');
        $('.success-badge').fadeOut(300, function() {
            $(this).remove();
        });
    }, 2000);
    
    // 添加震动效果提醒用户
    if (navigator.vibrate) {
        navigator.vibrate([100, 50, 100]);
    }
}

// 下载图片
function downloadImage() {
    if (!processedImageBlob) {
        showError('没有可下载的处理后图片');
        return;
    }

    try {
        const url = URL.createObjectURL(processedImageBlob);
        const a = document.createElement('a');
        a.href = url;
        
        // 生成有意义的文件名
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:.]/g, '-');
        a.download = `docuscan_enhanced_${timestamp}.jpg`;
        
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showSuccess('📥 图片下载完成！已保存到下载文件夹');
        
        // 添加下载反馈动画
        showDownloadSuccess();
        
        // 下载统计（可选）
        trackDownload();
        
    } catch (error) {
        showError('下载失败，请重试');
        console.error('Download error:', error);
    }
}

// 重置工具
function resetTool() {
    // 重置数据
    currentImageData = null;
    processedImageBlob = null;
    
    // 显示上传区域，隐藏原始图片容器
    $('#pasteArea').show();
    $('#originalImageContainer').hide();
    
    // 隐藏处理容器和结果容器，显示无图片占位符
    $('#processingContainer').hide();
    $('#processedImageContainer').hide().removeClass('fade-in processing-complete');
    $('#noImagePlaceholder').show();
    
    // 重置处理进度
    $('#processingProgress').css('width', '0%');
    $('#processingStep').text('正在初始化...');
    
    // 重置文件输入
    $('#fileInput').val('');
    
    // 隐藏提示
    hideAlerts();
    
    // 重置上传区域
    hideImageLoadingState();
    
    // 平滑滚动到顶部
    smoothScrollTo('body');
    
    // 显示重置成功消息
    setTimeout(() => {
        showToast('🔄 已重置，选择新图片即可自动处理', 'info');
    }, 500);
}

// 显示错误消息
function showError(message) {
    $('#errorMessage').text(message);
    $('#errorAlert').show().addClass('fade-in');
    
    // 滚动到错误消息
    setTimeout(() => {
        smoothScrollTo('#errorAlert');
    }, 100);
    
    // 自动隐藏
    setTimeout(() => {
        $('#errorAlert').fadeOut();
    }, 8000);
}

// 显示成功消息
function showSuccess(message) {
    $('#successMessage').text(message);
    $('#successAlert').show().addClass('fade-in');
    
    // 自动隐藏
    setTimeout(() => {
        $('#successAlert').fadeOut();
    }, 5000);
}

// 隐藏所有提示
function hideAlerts() {
    $('#errorAlert, #successAlert').hide().removeClass('fade-in');
}

// 显示处理遮罩
function showProcessingOverlay() {
    // 不再显示处理遮罩，因为已经有了对比UI中的进度显示
    // $('#processingOverlay').css('display', 'flex').hide().fadeIn(300);
}

// 隐藏处理遮罩
function hideProcessingOverlay() {
    // 不需要隐藏处理遮罩，因为没有显示
    // $('#processingOverlay').fadeOut(300);
}

// 显示图片放大模态框
function showImageModal(src) {
    const modalHtml = `
        <div class="modal fade" id="imageModal" tabindex="-1">
            <div class="modal-dialog modal-xl modal-dialog-centered">
                <div class="modal-content bg-transparent border-0">
                    <div class="modal-body p-0 text-center">
                        <img src="${src}" class="img-fluid" style="max-height: 90vh; border-radius: var(--border-radius);">
                        <button type="button" class="btn-close btn-close-white position-absolute top-0 end-0 m-3" 
                                data-bs-dismiss="modal"></button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除旧模态框，添加新的
    $('#imageModal').remove();
    $('body').append(modalHtml);
    $('#imageModal').modal('show');
    
    // 模态框关闭后清理
    $('#imageModal').on('hidden.bs.modal', function() {
        $(this).remove();
    });
}

// Toast通知
function showToast(message, type = 'info', duration = 3000) {
    const toastId = 'toast-' + Date.now();
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0" 
             id="${toastId}" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${icons[type]} ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // 创建toast容器（如果不存在）
    if ($('.toast-container').length === 0) {
        $('body').append(`
            <div class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 11000;"></div>
        `);
    }
    
    $('.toast-container').append(toastHtml);
    
    const toast = new bootstrap.Toast($('#' + toastId)[0], {
        delay: duration
    });
    
    toast.show();
    
    // 清理
    $('#' + toastId).on('hidden.bs.toast', function() {
        $(this).remove();
    });
}

// 平滑滚动
function smoothScrollTo(target) {
    const $target = $(target);
    if ($target.length) {
        $('html, body').animate({
            scrollTop: $target.offset().top - 100
        }, 800, 'easeInOutCubic');
    }
}

// 工具函数：格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// 工具函数：检测图片格式
function getImageFormat(dataUrl) {
    if (dataUrl.startsWith('data:image/jpeg')) return 'JPEG';
    if (dataUrl.startsWith('data:image/png')) return 'PNG';
    if (dataUrl.startsWith('data:image/gif')) return 'GIF';
    if (dataUrl.startsWith('data:image/webp')) return 'WEBP';
    if (dataUrl.startsWith('data:image/svg')) return 'SVG';
    if (dataUrl.startsWith('data:image/bmp')) return 'BMP';
    return 'Unknown';
}

// 显示下载成功反馈
function showDownloadSuccess() {
    const downloadBtn = $('.action-buttons .btn-success');
    const originalText = downloadBtn.html();
    
    // 短暂改变按钮状态
    downloadBtn.html('✅ 下载成功').addClass('btn-success-feedback');
    
    setTimeout(() => {
        downloadBtn.html(originalText).removeClass('btn-success-feedback');
    }, 2000);
}

// 下载统计（可选功能）
function trackDownload() {
    // 这里可以添加下载统计逻辑
    console.log('Image downloaded at:', new Date().toISOString());
}

// 页面离开确认
window.addEventListener('beforeunload', function(e) {
    if (currentImageData && !processedImageBlob) {
        e.preventDefault();
        e.returnValue = '您有未处理完成的图片，确定要离开吗？';
        return e.returnValue;
    }
});

// 错误处理
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showToast('页面出现错误，请刷新重试', 'error');
});

// 性能监控
window.addEventListener('load', function() {
    // 页面加载完成后的优化
    setTimeout(() => {
        // 预加载一些资源
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = '/process-image';
        document.head.appendChild(link);
    }, 2000);
});

// jQuery缓动函数扩展
$.extend($.easing, {
    easeInOutCubic: function(x, t, b, c, d) {
        if ((t /= d / 2) < 1) return c / 2 * t * t * t + b;
        return c / 2 * ((t -= 2) * t * t + 2) + b;
    }
});