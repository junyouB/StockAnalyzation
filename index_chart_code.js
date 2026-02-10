// 股票K线图和技术指标图表显示代码
// 从 frontend/index.html 中提取

// 图表初始化
function initChart() {
    try {
        // 检查echarts是否加载
        if (typeof echarts === 'undefined') {
            document.getElementById('error-message').textContent = 'ECharts库加载失败，请刷新页面重试';
            return null;
        }
        
        // 初始化图表
        const chart = echarts.init(document.getElementById('chart-container'));
        
        // 配置项
        const option = {
            title: {
                text: '股票K线图',
                left: 'center'
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            legend: {
                data: ['K线'],
                bottom: 10
            },
            dataZoom: [
                {
                    type: 'inside',
                    start: 0,
                    end: 100
                },
                {
                    show: true,
                    type: 'slider',
                    bottom: '0%',
                    start: 0,
                    end: 100
                }
            ],
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: [],
                axisLabel: {
                    rotate: 45
                }
            },
            yAxis: {
                type: 'value',
                scale: true
            },
            series: [
                {
                    name: 'K线',
                    type: 'candlestick',
                    data: [],
                    itemStyle: {
                        color: '#ef5350',
                        color0: '#26a69a',
                        borderColor: '#ef5350',
                        borderColor0: '#26a69a'
                    },
                    // 调整蜡烛图样式，确保影线清晰可见
                    emphasis: {
                        itemStyle: {
                            color: '#ff5722',
                            color0: '#4caf50',
                            borderColor: '#ff5722',
                            borderColor0: '#4caf50'
                        }
                    }
                }
            ]
        };
        
        chart.setOption(option);
        return chart;
    } catch (error) {
        document.getElementById('error-message').textContent = `初始化错误: ${error.message}`;
        console.error('初始化错误:', error);
        return null;
    }
}

// 图表配置和数据更新
function updateChart(chart, data, stockCode, chineseDates) {
    if (!chart) return;
    
    const dates = [];
    const klineData = [];
    const volumeData = [];
    
    data.forEach(item => {
        dates.push(item.date);
        // 确保数据类型为数字，并按ECharts要求的顺序：[open, close, low, high]
        klineData.push([
            parseFloat(item.open),
            parseFloat(item.close),
            parseFloat(item.low),
            parseFloat(item.high)
        ]);
        // 提取成交量数据
        volumeData.push(parseFloat(item.volume));
    });
    
    // 计算MA
    const ma5 = calculateMA(klineData, 5);
    const ma10 = calculateMA(klineData, 10);
    const ma20 = calculateMA(klineData, 20);
    const ma30 = calculateMA(klineData, 30);
    const ma60 = calculateMA(klineData, 60);
    
    // 计算成交量均线
    const volMA5 = calculateVolumeMA(volumeData, 5);
    const volMA10 = calculateVolumeMA(volumeData, 10);
    
    // 计算MACD
    const macdResult = calculateMACD(klineData);
    
    // 计算KDJ
    const kdjResult = calculateKDJ(klineData);
    
    // 计算RSI
    const rsi14 = calculateRSI(klineData, 14);
    
    // 计算BOLL
    const bollResult = calculateBOLL(klineData);
    
    // 计算技术指标分析结果
    const titleText = `股票K线图 - ${stockCode}`;
    const singleResult = {
        'MACD': analyzeMACD(macdResult),
        'RSI': analyzeRSI(rsi14),
        'KDJ': analyzeKDJ(kdjResult),
        'BOLL': analyzeBOLL(bollResult, klineData)
    };
    const compositeResult = analyzeComposite(singleResult);
    
    // 更新图表
    chart.setOption({
        title: [
            {
                text: titleText,
                left: 'center',
                top: '0%',
                subtext: `综合判断: ${compositeResult} | 买入信号: ${Object.values(singleResult).filter(s => s === '买入').length} | 卖出信号: ${Object.values(singleResult).filter(s => s === '卖出').length}`,
                subtextStyle: {
                    fontSize: 12,
                    color: compositeResult === '买入' ? '#4CAF50' : compositeResult === '卖出' ? '#f44336' : '#ff9800'
                }
            },
            {
                text: 'MA',
                left: '25%',
                top: '23%',
                textAlign: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            {
                text: 'MACD',
                left: '75%',
                top: '23%',
                textAlign: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            {
                text: 'VOL',
                left: '25%',
                top: '44%',
                textAlign: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            {
                text: 'KDJ',
                left: '75%',
                top: '44%',
                textAlign: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            {
                text: 'RSI',
                left: '25%',
                top: '66%',
                textAlign: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            {
                text: 'BOLL',
                left: '75%',
                top: '66%',
                textAlign: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            }
        ],
        
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            },
            formatter: function(params) {
                const index = params[0].dataIndex;
                let result = chineseDates[index] + '<br/>';
                
                // 处理K线数据
                if (params[0].seriesName === 'K线') {
                    const data = params[0].data;
                    result += `开盘: ${data[0]}<br/>`;
                    result += `收盘: ${data[1]}<br/>`;
                    result += `最低: ${data[2]}<br/>`;
                    result += `最高: ${data[3]}<br/>`;
                }
                
                // 处理MA数据
                params.forEach(param => {
                    if (param.seriesName.includes('MA')) {
                        result += `${param.seriesName}: ${param.value}<br/>`;
                    }
                });
                
                // 处理成交量数据
                params.forEach(param => {
                    if (param.seriesName === '成交量' || param.seriesName.includes('VOL')) {
                        result += `${param.seriesName}: ${param.value}<br/>`;
                    }
                });
                
                // 处理MACD数据
                const hasMACD = params.some(param => param.seriesName === 'DIF' || param.seriesName === 'DEA' || param.seriesName === 'MACD');
                if (hasMACD) {
                    result += '<br/><b>MACD指标说明:</b><br/>';
                    result += 'DIF: 快速与慢速移动平均线的差<br/>';
                    result += 'DEA: DIF的移动平均线<br/>';
                    result += 'MACD: (DIF-DEA)×2，反映动量变化<br/>';
                    result += '金叉: DIF上穿DEA，可能的买入信号<br/>';
                    result += '死叉: DIF下穿DEA，可能的卖出信号<br/><br/>';
                    params.forEach(param => {
                        if (param.seriesName === 'DIF' || param.seriesName === 'DEA' || param.seriesName === 'MACD') {
                            result += `${param.seriesName}: ${param.value}<br/>`;
                        }
                    });
                }
                
                // 处理RSI数据
                const hasRSI = params.some(param => param.seriesName === 'RSI14');
                if (hasRSI) {
                    result += '<br/><b>RSI指标说明:</b><br/>';
                    result += '相对强弱指标，取值范围0-100<br/>';
                    result += 'RSI > 70: 超买区域，可能回调<br/>';
                    result += 'RSI < 30: 超卖区域，可能反弹<br/>';
                    result += 'RSI在50左右: 市场处于平衡状态<br/><br/>';
                    params.forEach(param => {
                        if (param.seriesName === 'RSI14') {
                            result += `${param.seriesName}: ${param.value}<br/>`;
                        }
                    });
                }
                
                // 处理KDJ数据
                const hasKDJ = params.some(param => param.seriesName === 'K' || param.seriesName === 'D' || param.seriesName === 'J');
                if (hasKDJ) {
                    result += '<br/><b>KDJ指标说明:</b><br/>';
                    result += 'K线: 快速随机指标<br/>';
                    result += 'D线: 慢速随机指标<br/>';
                    result += 'J线: K和D的乖离率<br/>';
                    result += '金叉: K上穿D，可能的买入信号<br/>';
                    result += '死叉: K下穿D，可能的卖出信号<br/><br/>';
                    params.forEach(param => {
                        if (param.seriesName === 'K' || param.seriesName === 'D' || param.seriesName === 'J') {
                            result += `${param.seriesName}: ${param.value}<br/>`;
                        }
                    });
                }
                
                return result;
            }
        },
        
        // 其他配置项和系列数据...
        // 完整的图表配置和数据系列定义
        // 包括K线、MA、成交量、MACD、RSI、KDJ、BOLL等指标
    });
}

// 辅助函数
function calculateMA(data, period) {
    const result = [];
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            result.push(null);
            continue;
        }
        let sum = 0;
        for (let j = 0; j < period; j++) {
            sum += data[i - j][1]; // close price
        }
        result.push((sum / period).toFixed(2));
    }
    return result;
}

function calculateVolumeMA(data, period) {
    const result = [];
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            result.push(null);
            continue;
        }
        let sum = 0;
        for (let j = 0; j < period; j++) {
            sum += data[i - j];
        }
        result.push((sum / period).toFixed(2));
    }
    return result;
}

function calculateRSI(data, period = 14) {
    const result = [];
    let gains = [];
    let losses = [];
    
    // 计算每日涨跌幅度
    for (let i = 1; i < data.length; i++) {
        const change = data[i][1] - data[i-1][1];
        if (change > 0) {
            gains.push(change);
            losses.push(0);
        } else {
            gains.push(0);
            losses.push(Math.abs(change));
        }
    }
    
    // 计算RSI
    for (let i = 0; i < data.length; i++) {
        if (i < period) {
            result.push(null);
            continue;
        }
        
        // 计算平均 gain 和平均 loss
        let avgGain = 0;
        let avgLoss = 0;
        for (let j = 0; j < period; j++) {
            avgGain += gains[i-1-j];
            avgLoss += losses[i-1-j];
        }
        avgGain /= period;
        avgLoss /= period;
        
        // 计算RSI
        let rsi;
        if (avgLoss === 0) {
            rsi = 100;
        } else {
            const rs = avgGain / avgLoss;
            rsi = 100 - (100 / (1 + rs));
        }
        
        result.push(rsi.toFixed(2));
    }
    
    return result;
}

function calculateKDJ(data, period = 9, kPeriod = 3, dPeriod = 3) {
    const lowList = [];
    const highList = [];
    const rsvList = [];
    const kList = [];
    const dList = [];
    const jList = [];
    
    // 计算每个周期的最高价和最低价
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            lowList.push(data[i][2]); // low
            highList.push(data[i][3]); // high
            rsvList.push(null);
            kList.push(null);
            dList.push(null);
            jList.push(null);
        } else {
            // 计算period周期内的最高价和最低价
            let periodLow = Infinity;
            let periodHigh = -Infinity;
            for (let j = 0; j < period; j++) {
                periodLow = Math.min(periodLow, data[i-j][2]);
                periodHigh = Math.max(periodHigh, data[i-j][3]);
            }
            lowList.push(periodLow);
            highList.push(periodHigh);
            
            // 计算RSV
            const close = data[i][1];
            let rsv;
            if (periodHigh === periodLow) {
                rsv = 50;
            } else {
                rsv = ((close - periodLow) / (periodHigh - periodLow)) * 100;
            }
            rsvList.push(rsv.toFixed(2));
            
            // 计算K、D、J
            let k, d, j;
            if (i === period - 1) {
                // 第一个计算点
                k = rsv;
                d = rsv;
            } else {
                k = (2/3) * parseFloat(kList[i-1]) + (1/3) * rsv;
                d = (2/3) * parseFloat(dList[i-1]) + (1/3) * k;
            }
            j = 3 * k - 2 * d;
            
            kList.push(k.toFixed(2));
            dList.push(d.toFixed(2));
            jList.push(j.toFixed(2));
        }
    }
    
    return { k: kList, d: dList, j: jList };
}

function calculateBOLL(data, period = 20, multiplier = 2) {
    const maList = [];
    const upperList = [];
    const lowerList = [];
    
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            maList.push(null);
            upperList.push(null);
            lowerList.push(null);
        } else {
            // 计算MA
            let sum = 0;
            for (let j = 0; j < period; j++) {
                sum += data[i-j][1]; // close
            }
            const ma = sum / period;
            maList.push(ma.toFixed(2));
            
            // 计算标准差
            let variance = 0;
            for (let j = 0; j < period; j++) {
                variance += Math.pow(data[i-j][1] - ma, 2);
            }
            const stdDev = Math.sqrt(variance / period);
            
            // 计算上轨和下轨
            const upper = ma + multiplier * stdDev;
            const lower = ma - multiplier * stdDev;
            upperList.push(upper.toFixed(2));
            lowerList.push(lower.toFixed(2));
        }
    }
    
    return { ma: maList, upper: upperList, lower: lowerList };
}

function calculateMACD(data, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
    const ema12 = [];
    const ema26 = [];
    const dif = [];
    const dea = [];
    const macd = [];
    
    // 计算EMA12和EMA26
    for (let i = 0; i < data.length; i++) {
        const close = data[i][1];
        
        if (i === 0) {
            ema12.push(close);
            ema26.push(close);
        } else {
            const k12 = 2 / (fastPeriod + 1);
            const k26 = 2 / (slowPeriod + 1);
            ema12.push((close - ema12[i - 1]) * k12 + ema12[i - 1]);
            ema26.push((close - ema26[i - 1]) * k26 + ema26[i - 1]);
        }
        
        dif.push(ema12[i] - ema26[i]);
    }
    
    // 计算DEA和MACD
    for (let i = 0; i < dif.length; i++) {
        if (i === 0) {
            dea.push(dif[i]);
        } else {
            const k = 2 / (signalPeriod + 1);
            dea.push((dif[i] - dea[i - 1]) * k + dea[i - 1]);
        }
        macd.push((dif[i] - dea[i]) * 2);
    }
    
    return { dif, dea, macd };
}

// 分析函数
function analyzeMACD(macdResult) {
    const dif = macdResult.dif;
    const dea = macdResult.dea;
    
    if (dif.length < 2) return '观望';
    
    const lastDif = parseFloat(dif[dif.length - 1]);
    const lastDea = parseFloat(dea[dea.length - 1]);
    const prevDif = parseFloat(dif[dif.length - 2]);
    const prevDea = parseFloat(dea[dea.length - 2]);
    
    // 金叉：DIF上穿DEA
    if (prevDif <= prevDea && lastDif > lastDea) {
        return '买入';
    }
    // 死叉：DIF下穿DEA
    if (prevDif >= prevDea && lastDif < lastDea) {
        return '卖出';
    }
    // DIF在DEA上方，且MACD柱状图为正
    if (lastDif > lastDea && lastDif > 0) {
        return '买入';
    }
    // DIF在DEA下方，且MACD柱状图为负
    if (lastDif < lastDea && lastDif < 0) {
        return '卖出';
    }
    
    return '观望';
}

function analyzeRSI(rsiData) {
    if (!rsiData || rsiData.length === 0) return '观望';
    
    const lastRSI = parseFloat(rsiData[rsiData.length - 1]);
    
    if (lastRSI > 70) {
        return '卖出';
    } else if (lastRSI < 30) {
        return '买入';
    } else if (lastRSI > 50) {
        return '买入';
    } else {
        return '卖出';
    }
}

function analyzeKDJ(kdjResult) {
    const k = kdjResult.k;
    const d = kdjResult.d;
    const j = kdjResult.j;
    
    if (k.length < 2) return '观望';
    
    const lastK = parseFloat(k[k.length - 1]);
    const lastD = parseFloat(d[d.length - 1]);
    const lastJ = parseFloat(j[j.length - 1]);
    const prevK = parseFloat(k[k.length - 2]);
    const prevD = parseFloat(d[d.length - 2]);
    
    // 金叉：K上穿D
    if (prevK <= prevD && lastK > lastD) {
        return '买入';
    }
    // 死叉：K下穿D
    if (prevK >= prevD && lastK < lastD) {
        return '卖出';
    }
    // J值判断
    if (lastJ > 100) {
        return '卖出';
    } else if (lastJ < 0) {
        return '买入';
    }
    
    return '观望';
}

function analyzeBOLL(bollResult, klineData) {
    const upper = bollResult.upper;
    const middle = bollResult.ma;
    const lower = bollResult.lower;
    
    if (!upper || upper.length === 0) return '观望';
    
    const lastIndex = upper.length - 1;
    const lastUpper = parseFloat(upper[lastIndex]);
    const lastMiddle = parseFloat(middle[lastIndex]);
    const lastLower = parseFloat(lower[lastIndex]);
    const lastClose = parseFloat(klineData[lastIndex][1]);
    
    // 价格突破上轨
    if (lastClose > lastUpper) {
        return '买入';
    }
    // 价格跌破下轨
    if (lastClose < lastLower) {
        return '卖出';
    }
    // 价格在中轨上方
    if (lastClose > lastMiddle) {
        return '买入';
    }
    // 价格在中轨下方
    if (lastClose < lastMiddle) {
        return '卖出';
    }
    
    return '观望';
}

function analyzeComposite(singleResult) {
    const buySignals = Object.values(singleResult).filter(s => s === '买入').length;
    const sellSignals = Object.values(singleResult).filter(s => s === '卖出').length;
    
    if (buySignals >= 3) {
        return '买入';
    } else if (sellSignals >= 3) {
        return '卖出';
    } else if (buySignals > sellSignals) {
        return '买入';
    } else if (sellSignals > buySignals) {
        return '卖出';
    } else {
        return '观望';
    }
}
