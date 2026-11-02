// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
import './app.css'
import { mount } from 'svelte'
import App from './App.svelte'

export default mount(App, { target: document.getElementById('app') })
