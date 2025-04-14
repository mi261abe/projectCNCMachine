const API_URL = 'http://localhost:8080'

const runPythonScripts = async (scripts, plots, consoleOutput, state) => {
  const sendScripts = scripts.map(el => el.skript);
  let isResetNameSpace = true;

  console.log('runPythonScripts')
  for (let i = 0; i < sendScripts.length; i++) {
    const script = sendScripts[i];
    const res = await fetch(`${API_URL}/script`, {
      method: 'POST',
      mode: 'cors',
      cache: 'no-cache',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json'
      },
      redirect: 'follow',
      referrerPolicy: 'no-referrer',
      body: JSON.stringify({script: script, isResetNameSpace})
    })

    state.progress = i;
    isResetNameSpace = false
    console.log('res', res)
    const payload = await res.json();
    console.log('data', payload)

    plots.push(payload.plot ? payload.plot : {width: 600, height: 500});
    const consoleText = payload.console + payload.error;
    consoleOutput.push(consoleText ? consoleText : "");
  }
}

const fetchData = async () => {
  const res = await fetch(`${API_URL}/initData`)
  return await res.json();
}

const fetchInitialScript = async () => {
  const res = await fetch(`${API_URL}/initialScript`)
  return await res.text();
}

const saveInitialScript = async (initialScript) => {
  await fetch(`${API_URL}/initialScript`, {
    method: 'POST',
    mode: 'cors',
    cache: 'no-cache',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json'
    },
    redirect: 'follow',
    referrerPolicy: 'no-referrer',
    body: JSON.stringify({initialScript})
  })
}

const saveOrUpdateScript = async (scriptName, scriptText) => {
  await fetch(`${API_URL}/createOrUpdateScript`, {
    method: 'POST',
    mode: 'cors',
    cache: 'no-cache',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json'
    },
    redirect: 'follow',
    referrerPolicy: 'no-referrer',
    body: JSON.stringify({scriptName, scriptText})
  })
}

const deleteScript = async (scriptName) => {
  await fetch(`${API_URL}/deleteScript`, {
    method: 'POST',
    mode: 'cors',
    cache: 'no-cache',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json'
    },
    redirect: 'follow',
    referrerPolicy: 'no-referrer',
    body: JSON.stringify({scriptName})
  })
}

module.exports= {runPythonScripts, fetchData, fetchInitialScript, saveInitialScript, saveOrUpdateScript, deleteScript};