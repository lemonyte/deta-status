function responseChart(chart) {
  const scales = {
    x: {
      grid: { color: "rgba(52, 58, 64, 0.3)" },
      ticks: {
        // Needs a little bit of work ig
        callback: (context) => {
          const labelTime = (() => {
            if ((chart = "response-chart__base")) {
              return baseTimestampLabel;
            }
            if ((chart = "response-chart__drive")) {
              return driveTimestampLabel;
            }
            if ((chart = "response-chart__micro")) {
              return microTimestampLabel;
            }
          })();

          try {
            if (labelTime[context].endsWith("00:00")) {
              return labelTime[context].split(",")[1].slice(0, -5);
            } else if (labelTime[context].endsWith(":00") && parseInt(labelTime[context].slice(-5)) % 3 == 0) {
              return labelTime[context].split(",")[2];
            }
          } catch (error) {}
        },
      },
    },

    y: {
      position: "left",
      grid: { color: "rgba(52, 58, 64, 0.3)" },
    },

    y1: {
      position: "right",
    },
  };

  const options = {
    maintainAspectRatio: false,
    elements: {
      line: { tension: 0.1 },
      point: { radius: 0 },
    },
    hoverBackgroundColor: "white",
    hoverBorderColor: "rgba(239, 57, 168, 0.4)",
    pointHoverRadius: 4,
    pointHoverBorderWidth: 6,
    interaction: {
      intersect: false,
      mode: "index",
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        displayColors: false,
        callbacks: {
          label: (context) => context.formattedValue + " ms",
        },
      },
    },
    scales: scales,
  };

  const config = {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          borderColor: "rgb(239, 57, 168)",
          borderWidth: 2,
          data: [],
          yAxisID: "y",
        },
        {
          borderColor: "rgb(239, 57, 168)",
          borderWidth: 2,
          data: [],
          yAxisID: "y1",
        },
      ],
    },
    options: options,
    plugins: [
      {
        beforeDraw: (chart) => {
          if (chart.tooltip?._active?.length) {
            const x = chart.tooltip._active[0].element.x;
            const yAxis = chart.scales.y;
            const ctx = chart.ctx;
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(x, yAxis.top);
            ctx.lineTo(x, yAxis.bottom);
            ctx.lineWidth = 1;
            ctx.strokeStyle = "rgb(239, 57, 168)";
            ctx.stroke();
            ctx.restore();
          }
        },
      },
    ],
  };

  return new Chart(document.getElementById(chart), config);
}

function uptimeChart(chart) {
  const config = {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          data: [],
          borderRadius: 4,
          borderSkipped: false,
          backgroundColor: [],
          hoverBackgroundColor: "rgb(73, 80, 87)",
        },
      ],
    },

    options: {
      maintainAspectRatio: false,
      scales: {
        x: {
          ticks: { display: false },
        },
        y: {
          display: false,
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          enabled: false,
          external: externalTooltipHandler,
        },
      },
    },
  };

  return new Chart(document.getElementById(chart), config);
}

function getOrCreateTooltip(chart) {
  let tooltipElement = chart.canvas.parentNode.querySelector("div");
  if (!tooltipElement) {
    tooltipElement = document.createElement("div");
    tooltipElement.classList.add("tooltip__design");
    tooltipUL = document.createElement("ul");
    tooltipUL.classList.add("tooltip__ul");

    tooltipElement.appendChild(tooltipUL);
    chart.canvas.parentNode.appendChild(tooltipElement);
  }
  return tooltipElement;
}

function externalTooltipHandler(context) {
  const { chart, tooltip } = context;
  const tooltipElement = getOrCreateTooltip(chart);

  if (tooltip.opacity === 0) {
    tooltipElement.style.opacity = 0;
    return;
  }

  const tooltipRightCalc = (window.innerWidth + context.chart.chartArea.width) / 2 - context.tooltip.caretX;
  const tooltipLeftCalc = (window.innerWidth - context.chart.chartArea.width) / 2 + context.tooltip.caretX;

  if (tooltipRightCalc < 94) {
    tooltipElement.style.marginLeft = `${tooltipRightCalc - 94}px`;
    tooltipElement.style.setProperty("--margin", `${-10 - (tooltipRightCalc - 94)}px`);
  } else if (tooltipLeftCalc < 94) {
    tooltipElement.style.marginLeft = `${tooltipRightCalc - (window.innerWidth - 94)}px`;
    tooltipElement.style.setProperty("--margin", `${-10 - (tooltipRightCalc - (window.innerWidth - 94))}px`);
  } else {
    tooltipElement.style.marginLeft = "0px";
    tooltipElement.style.setProperty("--margin", "-10px");
  }

  if (tooltip.body) {
    const titleLines = tooltip.title || [];
    const bodyLines = tooltip.body.map((b) => b.lines);
    const tooltipLI = document.createElement("li");
    const tooltipUL = tooltipElement.getElementsByClassName("tooltip__ul")[0];
    titleLines.forEach((title) => {
      const tooltipSPAN = document.createElement("span");
      const tooltipTitle = document.createTextNode(title);

      tooltipUL.appendChild(tooltipLI);
      tooltipLI.appendChild(tooltipSPAN);
      tooltipSPAN.appendChild(tooltipTitle);
    });

    const tooltipBodyP = document.createElement("p");
    bodyLines.forEach((body, i) => {
      const colors = tooltip.labelColors[i];
      const colorSquare = document.createElement("span");
      colorSquare.classList.add("colorSquare");
      colorSquare.style.background = colors.backgroundColor;
      colorSquare.style.border = colors.borderColor;
      const textLabel = document.createTextNode(body);

      tooltipBodyP.appendChild(colorSquare);
      tooltipBodyP.appendChild(textLabel);
    });

    const ULnode = tooltipElement.querySelector("ul");
    while (ULnode.firstChild) {
      ULnode.firstChild.remove();
    }
    ULnode.appendChild(tooltipLI);
    tooltipLI.appendChild(tooltipBodyP);
    tooltipElement.style.opacity = 1;

    tooltipElement.style.left = chart.canvas.offsetLeft + tooltip.caretX + "px";
    tooltipElement.style.font = tooltip.options.padding + "px" + tooltip.options.padding + "px";
  }
}

function parseTimestamp(timestamp) {
  const time = new Date(timestamp * 1000);
  return `${time.toLocaleDateString("default", {
    weekday: "short",
    month: "short",
    day: "2-digit",
  })} ${time.getFullYear()}, ${time.toLocaleTimeString("default", {
    hour: "2-digit",
    hourCycle: "h23",
    minute: "2-digit",
  })}`;
}

function parseTestsData(testsData) {
  let count = 0;
  for (const key in testsData) {
    if (testsData[key].passed == true) {
      count++;
    }
  }
  return count / Object.keys(testsData).length;
}

function fillMissingDataPoints(timestamp, responseTime, statusData) {
  let durationGap;
  let missingDataNumber;
  for (i = 0; i < timestamp.length; i++) {
    durationGap = timestamp[i + 1] - timestamp[i];
    missingDataNumber = Math.round(durationGap / 600) - 1;
    if (durationGap > 960 && missingDataNumber > 0) {
      while (missingDataNumber > 0) {
        timestamp.splice(i + 1, 0, timestamp[i + 1] - 600);
        responseTime.splice(i + 1, 0, null);
        statusData.splice(i + 1, 0, 0);
        missingDataNumber--;
      }
    }
  }
}

async function getData(region) {
  const responses = await Promise.all([
    fetch(`https://status-${region}.deta.dev/results/base`),
    fetch(`https://status-${region}.deta.dev/results/drive`),
    fetch(`https://status-${region}.deta.dev/results/micro`),
  ]);

  const data = await Promise.all(responses.map((r) => r.json()));

  const baseTimestamp = data[0].map((x) => x.timestamp);
  // const baseResponseData = data[0].map((x) => parseInt(x.duration * 1000));
  const baseResponseData = data[0].map((x) => parseInt(x.tests.ping.details.average_response_time * 1000));
  const baseStatusData = data[0].map((x) => parseTestsData(x.tests));
  const driveTimestamp = data[1].map((x) => x.timestamp);
  // const driveResponseData = data[1].map((x) => parseInt(x.duration * 1000));
  const driveResponseData = data[1].map((x) => parseInt(x.tests.ping.details.average_response_time * 1000));
  const driveStatusData = data[1].map((x) => parseTestsData(x.tests));
  const microTimestamp = data[2].map((x) => x.timestamp);
  // const microResponseData = data[2].map((x) => parseInt(x.duration * 1000));
  const microResponseData = data[2].map((x) => parseInt(x.tests.ping.details.average_response_time * 1000));
  const microStatusData = data[2].map((x) => parseTestsData(x.tests));

  fillMissingDataPoints(baseTimestamp, baseResponseData, baseStatusData);
  fillMissingDataPoints(driveTimestamp, driveResponseData, driveStatusData);
  fillMissingDataPoints(microTimestamp, microResponseData, microStatusData);

  baseTimestampLabel = baseTimestamp.slice(-144).map((x) => parseTimestamp(x));
  baseResponseTime = baseResponseData.slice(-144);
  baseUptimeData = baseStatusData.slice(-144);

  driveTimestampLabel = driveTimestamp.slice(-144).map((x) => parseTimestamp(x));
  driveResponseTime = driveResponseData.slice(-144);
  driveUptimeData = driveStatusData.slice(-144);

  microTimestampLabel = microTimestamp.slice(-144).map((x) => parseTimestamp(x));
  microResponseTime = microResponseData.slice(-144);
  microUptimeData = microStatusData.slice(-144);

  currentStatusUpdate();
}

function currentStatusUpdate() {
  const currentStatusStyle = document.getElementById("current-status");
  const currentStatus = document.getElementById("current-status__text");
  const currentUptime = [baseUptimeData.slice(-1)[0], driveUptimeData.slice(-1)[0], microUptimeData.slice(-1)[0]];

  if (currentUptime.every((value) => value === 1)) {
    currentStatus.innerHTML = "All Systems Operational";
    currentStatusStyle.style.backgroundColor = "rgb(39, 163, 0)";
  } else if (currentUptime.every((value) => value === 0)) {
    currentStatus.innerHTML = "All Systems Not Operational";
    currentStatusStyle.style.backgroundColor = "rgb(186, 12, 12)";
  } else {
    currentStatus.innerHTML = "Some Systems Not Operational";
    currentStatusStyle.style.backgroundColor = "rgb(255, 165, 0)";
  }
}

async function updateData() {
  const GERMANY = document.getElementById("radio--germany");
  const INDIA = document.getElementById("radio--india");
  const SINGAPORE = document.getElementById("radio--singapore");
  const BRAZIL = document.getElementById("radio--brazil");
  const US = document.getElementById("radio--us");

  const regionsArray = [GERMANY, INDIA, SINGAPORE, BRAZIL, US];
  let currentRegion = "";
  for (let i = 0; i < regionsArray.length; i++) {
    if (regionsArray[i].checked == true) {
      await getData(`${regionsArray[i].value}`);
      currentRegion = `${regionsArray[i].value}`;
    }
  }

  chartUpdate(dataMargin(), currentRegion);
}

function uptimeTooltipData(chart, data) {
  chart.options.plugins.tooltip.callbacks.label = (context) => {
    const percentPassed = parseInt(data[context.dataIndex] * 100);
    if (percentPassed == 100) {
      return "All tests passed.";
    } else if (percentPassed == 0) {
      return "All tests failed.";
    } else {
      return `${percentPassed}% of tests passed.`;
    }
  };
}

function uptimeBackgroundColor(statusData) {
  const uptimeColors = [];
  for (i = 0; i < statusData.length; i++) {
    if (statusData[i] == 1) {
      uptimeColors.push("rgb(39, 163, 0)");
    } else if (statusData[i] == 0) {
      uptimeColors.push("rgb(186, 12, 12)");
    } else {
      uptimeColors.push("rgb(255, 165, 0)");
    }
  }
  return uptimeColors;
}

function averageResponseTime(htmlID, responseTime) {
  responseTime = responseTime.filter((x) => x);
  const average = responseTime.reduce((a, b) => a + b, 0) / responseTime.length;
  document.getElementById(htmlID).innerHTML = `${Math.round(average)} ms`;
}

function dataMargin() {
  const currentWidth = window.innerWidth;
  if (currentWidth <= 650) {
    return 48;
  } else if (currentWidth > 650 && currentWidth <= 1000) {
    return 96;
  } else {
    return 144;
  }
}

function chartUpdate(margin, region) {
  if (currentDataMargin === margin && currentSelectedRegion === region) {
    return;
  }
  currentDataMargin = margin;
  currentSelectedRegion = region;

  baseResponseChart.data.labels = baseTimestampLabel.slice(-margin);
  driveResponseChart.data.labels = driveTimestampLabel.slice(-margin);
  microResponseChart.data.labels = microTimestampLabel.slice(-margin);

  baseResponseChart.data.datasets[0].data = baseResponseTime.slice(-margin);
  baseResponseChart.data.datasets[1].data = baseResponseTime.slice(-margin);
  driveResponseChart.data.datasets[0].data = driveResponseTime.slice(-margin);
  driveResponseChart.data.datasets[1].data = driveResponseTime.slice(-margin);
  microResponseChart.data.datasets[0].data = microResponseTime.slice(-margin);
  microResponseChart.data.datasets[1].data = microResponseTime.slice(-margin);

  averageResponseTime("avg-response-time__base", baseResponseTime.slice(-margin));
  averageResponseTime("avg-response-time__drive", driveResponseTime.slice(-margin));
  averageResponseTime("avg-response-time__micro", microResponseTime.slice(-margin));

  baseUptimeChart.data.labels = baseTimestampLabel.slice(-margin);
  driveUptimeChart.data.labels = driveTimestampLabel.slice(-margin);
  microUptimeChart.data.labels = microTimestampLabel.slice(-margin);

  baseUptimeChart.data.datasets[0].backgroundColor = uptimeBackgroundColor(baseUptimeData.slice(-margin));
  driveUptimeChart.data.datasets[0].backgroundColor = uptimeBackgroundColor(driveUptimeData.slice(-margin));
  microUptimeChart.data.datasets[0].backgroundColor = uptimeBackgroundColor(microUptimeData.slice(-margin));

  baseUptimeChart.data.datasets[0].data = Array(baseUptimeData.slice(-margin).length).fill(1);
  driveUptimeChart.data.datasets[0].data = Array(driveUptimeData.slice(-margin).length).fill(1);
  microUptimeChart.data.datasets[0].data = Array(microUptimeData.slice(-margin).length).fill(1);

  uptimeChartFooter(baseUptimeData, "uptime-chart__percentage__base");
  uptimeChartFooter(driveUptimeData, "uptime-chart__percentage__drive");
  uptimeChartFooter(microUptimeData, "uptime-chart__percentage__micro");

  document.getElementById("uptime-chart-last__base").innerHTML =
    document.getElementById("uptime-chart-last__drive").innerHTML =
    document.getElementById("uptime-chart-last__micro").innerHTML =
      `${margin / 6} hours ago`;

  uptimeTooltipData(baseUptimeChart, baseUptimeData.slice(-margin));
  uptimeTooltipData(driveUptimeChart, driveUptimeData.slice(-margin));
  uptimeTooltipData(microUptimeChart, microUptimeData.slice(-margin));

  chartList.forEach((element) => element.update());
}

function uptimeChartFooter(statusData, elementID) {
  const allPassCount = statusData.slice(-currentDataMargin).reduce((a, v) => (v === 1 ? a + 1 : a), 0);
  const uptimePercentage = parseFloat((allPassCount / currentDataMargin) * 100).toFixed(2);
  document.getElementById(elementID).innerHTML = uptimePercentage + " % uptime";
}

let baseTimestampLabel = [],
  baseResponseTime = [],
  baseUptimeData = [],
  driveTimestampLabel = [],
  driveResponseTime = [],
  driveUptimeData = [],
  microTimestampLabel = [],
  microResponseTime = [],
  microUptimeData = [];

let currentDataMargin = 0;
let currentSelectedRegion = "";

const baseResponseChart = responseChart("response-chart__base");
const driveResponseChart = responseChart("response-chart__drive");
const microResponseChart = responseChart("response-chart__micro");

const baseUptimeChart = uptimeChart("uptime-chart__base");
const driveUptimeChart = uptimeChart("uptime-chart__drive");
const microUptimeChart = uptimeChart("uptime-chart__micro");

const chartList = [
  baseResponseChart,
  baseUptimeChart,
  driveResponseChart,
  driveUptimeChart,
  microResponseChart,
  microUptimeChart,
];

window.addEventListener("resize", () => {
  chartUpdate(dataMargin(), currentSelectedRegion);
});

document.getElementById("radio--germany").click();
