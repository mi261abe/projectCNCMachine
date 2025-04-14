const {fetchInitialScript, saveInitialScript} = require('./api');
const $ = require( "jquery" );

const initConfig = () => {
  $("#toConfigBtn").click(() => goToConfig())
}

const goToConfig = async () => {
  $("#wrapper").addClass('hide');
  $('#textAreas').addClass('hide');
  $('#tabSection').addClass('hide');
  const initScriptContent =  await fetchInitialScript()
  const initScript = `<div id="upperConfigWrapper"><h2>Initial Script</h2><div id="initScriptWrapper"><textarea id="initScript"/></div></div>`
  const saveButton = `<div id="saveBtnWrapper" class="saveBtnWrapper"><button id="saveBtn">Save</button></div>`
  $('#main').append(initScript)
  $('#main').append(saveButton)
  $('#initScript').val(initScriptContent)
  $('#saveBtn').click(() => saveScript())
  $("#toConfigBtn").html('Back')
  $("#toConfigBtn").off('click');
  $("#toConfigBtn").click(() => goBack())
}

const goBack = () => {
  $('#upperConfigWrapper').remove();
  $('#saveBtnWrapper').remove();
  $("#wrapper").removeClass('hide')
  $('#textAreas').removeClass('hide')
  $('#tabSection').removeClass('hide');
  $("#toConfigBtn").html('Configuration')
  $("#toConfigBtn").off('click');
  $("#toConfigBtn").click(() => goToConfig())
}

const saveScript = async () => {
  const script = $('#initScript').val()
  const confirmed = confirm('The page will be reloaded when you continue and all changes to scripts that have not been made permanently will be undone!')
  if (!confirmed) return;
  await saveInitialScript(script)
  window.location.reload();
}

module.exports={
  initConfig,
}