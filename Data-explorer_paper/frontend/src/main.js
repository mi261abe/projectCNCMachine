const {runPythonScripts, fetchData, saveOrUpdateScript, deleteScript} = require('./api')
const {initConfig} = require('./config')
const $ = require( "jquery" );
const mpld3 = require("mpld3")

let scripts = [];
let hasDataLoadedFirstTime = false;
let wasRunScriptsExecuted = false

const stateObject = {progress: 0, isLoading: false};
const changeStateHandler = {
  set(target, key, value) {
    if (key === 'progress') {
      target.progress = value;
      updateProcessBar(value);
    }
    if (key === 'isLoading') {
      if (value) startLoading();
      else stopLoading();
      target.isLoading = value;
    }
  }
};
const state = new Proxy(stateObject, changeStateHandler)

$(document).ready(function (){
  initConfig();
  initFirstTab();
  loadFirstTab();
});

const initFirstTab = () => {
  const tab = `<button id="button_tab0">Load Data</button>`
  $("#tabSection").append(tab)
  $(`#button_tab0`).click(() => goToTab(0));
  goToTab(0);
}

const loadFirstTab = () => {
  state.isLoading = true;
  fetchData().then(result => {
    console.log('result', result)
    if (result.error) throw Error(result.error)
    scripts = result.scripts;
    hasDataLoadedFirstTime = true
    createConsoleDisplay(0, result.console)
    if (result.plots.length) createChart(-1, result.plots[0])
    if (result.plots.length > 1) createChart(0, result.plots[1], true)
    goToTab(0);
    createTabs(scripts);
    state.isLoading = false;
  }).catch(error => {
    state.isLoading = false;
    displayError(error);
  });
}

const createChart = (tab, plot, hide = false) => {
  const chart = `<div id="graph${tab}"></div>`
  $(`#graph${tab}`).remove();
  $("#wrapper").append(chart);
  if (hide) $(`#graph${tab}`).addClass('hide');
  mpld3.draw_figure(`graph${tab}`, plot);
}

const createTabs = () => {
  console.log('createTabs', scripts)
  // create normal tabs
  scripts.forEach((script, idx) => {
    const tab = `<button id="button_tab${idx + 1}">${script.name}</button>`
    $("#tabSection").append(tab)
    $(`#button_tab${idx + 1}`).click(() => goToTab(idx + 1));
  })

  // create new script tab
  const newScriptTab = `<button id="newScriptTab">+ Add Step</button>`
  $("#tabSection").append(newScriptTab)
  $(`#newScriptTab`).click(() => goToNewScriptTab());
}

const createConsoleDisplay = (tab, content) => {
  $(`#consoleDisplay_${tab}`).remove()
  const consoleDisplay = `<textarea id="consoleDisplay_${tab}" class="consoleDisplay"/>`
  $('#textAreas').append(consoleDisplay)
  $(`#consoleDisplay_${tab}`).val(content)
  $(`#consoleDisplay_${tab}`).addClass('hide');
}

function goToTab(tab) {
  $("#container").empty();
  hideCharts();
  hideConsoleDisplays()
  toggleActiveClass(`button_tab${tab}`)

  if (tab === 0) {
    createContentFirstTab()
    $(`#graph${-1}`).removeClass('hide')
    $(`#consoleDisplay_${tab}`).removeClass('hide')
  } else {
    const content = `
    <div>
      <textarea id="pythonText"></textarea>
      <div class="saveBtnWrapper withMaxWith500">
        <button id="saveScriptBtn">Make changes permanent</button>
        <button id="removeScriptBtn">Remove script</button>
      </div>
    </div>
`
    if (wasRunScriptsExecuted) $("#wrapper").addClass("notFirstTab")
    else $("#wrapper").removeClass("notFirstTab")
    $("#container").append(content);
    $("#pythonText").val(scripts[tab - 1].skript);
    $("#pythonText").on('change', (e) => scripts[tab - 1].skript = e.target.value);
    $('#saveScriptBtn').click(() => saveScript(tab));
    $('#removeScriptBtn').click(() => removeScript(tab));

    if (wasRunScriptsExecuted) {
      $(`#graph${tab}`).removeClass('hide')
      $(`#graph${tab}`).addClass('secondChart')
      $(`#graph${tab - 1}`).removeClass('hide')
      $(`#graph${tab - 1}`).addClass('firstChart');
      $(`#consoleDisplay_${tab}`).removeClass('hide')
    }
  }
}

const createContentFirstTab = () => {
  if (hasDataLoadedFirstTime) {
    const content =  `<button id="runScripts">Run Scripts</button>`
    $("#container").append(content);
    $("#runScripts").click(() => runScripts());
  }
  $("#wrapper").removeClass("notFirstTab")
}

const hideCharts = () => {
  for(let i = -1; i <= scripts.length; i++) {
    $(`#graph${i}`).addClass('hide');
    $(`#graph${i}`).removeClass('secondChart')
    $(`#graph${i}`).removeClass('firstChart')
  }
}

const hideConsoleDisplays = () => {
  for(let i = 0; i <= scripts.length; i++) {
    $(`#consoleDisplay_${i}`).addClass('hide');
  }
}

const toggleActiveClass = (tabId) => {
  for (let i = 0; i < scripts.length + 1; i++) {
    $(`#button_tab${i}`).removeClass('active')
  }
  $(`#newScriptTab`).removeClass('active')
  $(`#${tabId}`).addClass('active')
}

const saveScript = async (tab) => {
  state.isLoading = true;
  await saveOrUpdateScript(scripts[tab - 1].name, scripts[tab - 1].skript);
  state.isLoading = false;
  goToTab(tab);
}

const removeScript = async (tab) => {
  const confirmed = confirm('Do you really want to delete this script permanently? The page will be reloaded when you continue and all changes on other scripts that have not been made permanently will be undone!')
  if (!confirmed) return;
  state.isLoading = true;
  await deleteScript(scripts[tab - 1].name);
  window.location.reload();
}

const goToNewScriptTab = () => {
  $("#container").empty();
  hideCharts();
  hideConsoleDisplays()
  toggleActiveClass(`newScriptTab`)
  $("#wrapper").removeClass("notFirstTab")

  const content = `
    <div>
      <h2>New Processing Step</h2>
      <div class="newScriptWrapper">
        <div>
          <div>
            <label for="newScriptName">Name for new step</label>
            <input type="text" id="newScriptName"/>.py
          </div>
          <div class="newScriptTextWrapper">
            <label for="newScriptText">Python Code</label>
            <textarea id="newScriptText"></textarea> 
          </div>
          <div id="saveNewScriptBtnWrapper" class="saveBtnWrapper">
            <button id="saveNewScriptBtn">Save</button>
          </div>
        </div>
      </div>
    </div>
`
  $("#container").append(content);
  $('#saveNewScriptBtn').click(() => addNewScript());
}

const addNewScript = async () => {
  $("#errorMsg").remove();
  const newScriptName = $('#newScriptName').val();
  const newScriptText = $('#newScriptText').val();
  if (!newScriptName || !newScriptText) {
    const errorMsg = `<div id="errorMsg">Error! Name or code missing!</div>`
    $("#saveNewScriptBtnWrapper").append(errorMsg);
    return;
  }
  const confirmed = confirm('The page will be reloaded when you continue and all changes on other scripts that have not been made permanently will be undone!')
  if (!confirmed) return;
  state.isLoading = true;
  await saveOrUpdateScript(newScriptName, newScriptText);
  window.location.reload();
}

const updateProcessBar = (progress) => {
  $('#progressBar').val(progress)
}

const runScripts = async () => {
  state.isLoading = true;
  const plots = [];
  const consoleOutput = []
  await runPythonScripts(scripts, plots, consoleOutput, state);
  wasRunScriptsExecuted = true;
  for (let i = 0; i < plots.length; i++) {
    createChart(i + 1, plots[i], true);
    createConsoleDisplay(i+1, consoleOutput[i])
  }
  goToTab(0);
  state.isLoading = false;
}

const startLoading = () => {
  hideCharts();
  hideConsoleDisplays();
  $('#toConfigBtn').prop('disabled', true);
  $("#container").addClass('hide');
  $("#tabSection").addClass('hide');
  $("#wrapper").addClass("loading")
  const loadingText = `<div id="loadingText"><div>Loading...</div><progress id="progressBar" value="0" max="${scripts.length}" /></div>`
  $("#wrapper").append(loadingText)
}

const stopLoading = () => {
  state.progress = scripts.length;
  $('#toConfigBtn').prop('disabled', false);
  $("#container").removeClass('hide')
  $("#tabSection").removeClass('hide')
  $("#wrapper").removeClass("loading")
  $("#loadingText").remove()
}

const displayError = (error) => {
  const consoleDisplay = `<textarea id="consoleDisplay_0" class="consoleDisplay"/>`
  $('#textAreas').append(consoleDisplay)
  $('#consoleDisplay_0').val(error.message)
}