// 画面に出す文は「日本語を鍵」に各言語を引く。
// 日本語ページ(<html lang="ja">)では t は素通しなので、挙動は従来と1ビットも変わらない。
// 翻訳を受け取るのは viewer/en/(EN) ・ viewer/pt/(PT, pt-BR) ・ viewer/es/(ES) だけ。
// 鍵が無ければ日本語のまま出す(消えるより良い)。新しい文言を足したら3つの表すべてに足す。
const EN = {
  // 動画ファイルの再生エラー (html-video-player.js)
  '動画の読み込みが中断されました。': 'Video loading was interrupted.',
  'ネットワークエラーで動画を読み込めませんでした。': 'A network error kept the video from loading.',
  '動画をデコードできませんでした。': 'The video could not be decoded.',
  'この動画形式またはURLはブラウザで再生できません。': 'This video format or URL cannot be played in this browser.',
  '動画を読み込めませんでした。': 'The video could not be loaded.',

  // YouTube のエラー (youtube-player.js)
  'YouTube APIの読み込みに失敗しました。': 'Failed to load the YouTube API.',
  'YouTube APIを読み込めませんでした。': 'The YouTube API could not be loaded.',
  'この動画は埋め込み再生が許可されていません。YouTubeで開いてください。':
    'This video does not allow embedded playback. Open it on YouTube.',
  'YouTube動画IDが正しくありません。': 'The YouTube video ID is not valid.',
  'このブラウザでは動画を再生できません。': 'This browser cannot play the video.',
  '動画が見つからないか、非公開になっています。': 'The video was not found or is private.',
  'YouTube動画を読み込めませんでした。': 'The YouTube video could not be loaded.',

  // 画質 (quality-gate.js / app.js)
  '240p以下': '240p or lower',
  '1080p超': 'Above 1080p',
  '自動調整': 'Auto',
  'YouTubeの現在の報告': 'YouTube currently reports',
  '映像をクリック／タップして操作バーを表示': 'Click or tap the video to show its control bar',

  // 操作まわり (app.js)
  '再生': 'Play',
  '一時停止': 'Pause',
  'YouTubeで開く ↗': 'Open on YouTube ↗',
  '動画を直接開く ↗': 'Open the video file ↗',
  'この動画はここでは再生できません': 'This video cannot be played here',
  '動画を読み込めませんでした': 'The video could not be loaded',
  '表示位置を保存できませんでした。': 'Could not save the view position.',
  '自動再生のためミュートで再生中です。Mで解除できます。': 'Muted for autoplay. Press M to unmute.',
  'YouTubeのURLまたは動画ファイル（mp4など）のURLを入力してください。':
    'Enter a YouTube URL or a video file URL (such as an mp4).',
  'フルスクリーン表示を開始できませんでした。': 'Could not enter fullscreen.',
};

const PT = {
  // 動画ファイルの再生エラー (html-video-player.js)
  '動画の読み込みが中断されました。': 'O carregamento do vídeo foi interrompido.',
  'ネットワークエラーで動画を読み込めませんでした。': 'Um erro de rede impediu o carregamento do vídeo.',
  '動画をデコードできませんでした。': 'Não foi possível decodificar o vídeo.',
  'この動画形式またはURLはブラウザで再生できません。': 'Este formato de vídeo ou URL não pode ser reproduzido neste navegador.',
  '動画を読み込めませんでした。': 'Não foi possível carregar o vídeo.',

  // YouTube のエラー (youtube-player.js)
  'YouTube APIの読み込みに失敗しました。': 'Falha ao carregar a API do YouTube.',
  'YouTube APIを読み込めませんでした。': 'Não foi possível carregar a API do YouTube.',
  'この動画は埋め込み再生が許可されていません。YouTubeで開いてください。':
    'Este vídeo não permite reprodução incorporada. Abra no YouTube.',
  'YouTube動画IDが正しくありません。': 'O ID do vídeo do YouTube não é válido.',
  'このブラウザでは動画を再生できません。': 'Este navegador não consegue reproduzir o vídeo.',
  '動画が見つからないか、非公開になっています。': 'O vídeo não foi encontrado ou é privado.',
  'YouTube動画を読み込めませんでした。': 'Não foi possível carregar o vídeo do YouTube.',

  // 画質 (quality-gate.js / app.js)
  '240p以下': '240p ou menos',
  '1080p超': 'Acima de 1080p',
  '自動調整': 'Automático',
  'YouTubeの現在の報告': 'O YouTube informa no momento',
  '映像をクリック／タップして操作バーを表示': 'Clique ou toque no vídeo para mostrar a barra de controles',

  // 操作まわり (app.js)
  '再生': 'Reproduzir',
  '一時停止': 'Pausar',
  'YouTubeで開く ↗': 'Abrir no YouTube ↗',
  '動画を直接開く ↗': 'Abrir o arquivo de vídeo ↗',
  'この動画はここでは再生できません': 'Este vídeo não pode ser reproduzido aqui',
  '動画を読み込めませんでした': 'Não foi possível carregar o vídeo',
  '表示位置を保存できませんでした。': 'Não foi possível salvar a posição da visualização.',
  '自動再生のためミュートで再生中です。Mで解除できます。': 'Sem som por causa da reprodução automática. Pressione M para ativar o som.',
  'YouTubeのURLまたは動画ファイル（mp4など）のURLを入力してください。':
    'Digite uma URL do YouTube ou de um arquivo de vídeo (como um mp4).',
  'フルスクリーン表示を開始できませんでした。': 'Não foi possível entrar em tela cheia.',
};

const ES = {
  // 動画ファイルの再生エラー (html-video-player.js)
  '動画の読み込みが中断されました。': 'Se interrumpió la carga del video.',
  'ネットワークエラーで動画を読み込めませんでした。': 'Un error de red impidió cargar el video.',
  '動画をデコードできませんでした。': 'No se pudo decodificar el video.',
  'この動画形式またはURLはブラウザで再生できません。': 'Este formato de video o URL no se puede reproducir en este navegador.',
  '動画を読み込めませんでした。': 'No se pudo cargar el video.',

  // YouTube のエラー (youtube-player.js)
  'YouTube APIの読み込みに失敗しました。': 'Falló la carga de la API de YouTube.',
  'YouTube APIを読み込めませんでした。': 'No se pudo cargar la API de YouTube.',
  'この動画は埋め込み再生が許可されていません。YouTubeで開いてください。':
    'Este video no permite la reproducción insertada. Ábrelo en YouTube.',
  'YouTube動画IDが正しくありません。': 'El ID del video de YouTube no es válido.',
  'このブラウザでは動画を再生できません。': 'Este navegador no puede reproducir el video.',
  '動画が見つからないか、非公開になっています。': 'No se encontró el video o es privado.',
  'YouTube動画を読み込めませんでした。': 'No se pudo cargar el video de YouTube.',

  // 画質 (quality-gate.js / app.js)
  '240p以下': '240p o menos',
  '1080p超': 'Más de 1080p',
  '自動調整': 'Automática',
  'YouTubeの現在の報告': 'YouTube informa en este momento',
  '映像をクリック／タップして操作バーを表示': 'Haz clic o toca el video para mostrar la barra de controles',

  // 操作まわり (app.js)
  '再生': 'Reproducir',
  '一時停止': 'Pausar',
  'YouTubeで開く ↗': 'Abrir en YouTube ↗',
  '動画を直接開く ↗': 'Abrir el archivo de video ↗',
  'この動画はここでは再生できません': 'Este video no se puede reproducir aquí',
  '動画を読み込めませんでした': 'No se pudo cargar el video',
  '表示位置を保存できませんでした。': 'No se pudo guardar la posición de la vista.',
  '自動再生のためミュートで再生中です。Mで解除できます。': 'Sin sonido por la reproducción automática. Presiona M para activarlo.',
  'YouTubeのURLまたは動画ファイル（mp4など）のURLを入力してください。':
    'Ingresa una URL de YouTube o de un archivo de video (como un mp4).',
  'フルスクリーン表示を開始できませんでした。': 'No se pudo activar la pantalla completa.',
};

// <html lang> の先頭2文字で表を選ぶ（pt-BR → pt、es-419 → es）。ja やその他は素通し。
const TABLES = { en: EN, pt: PT, es: ES };
const lang = (globalThis.document?.documentElement?.lang ?? 'ja').toLowerCase().slice(0, 2);
const table = TABLES[lang];

export const t = table ? (text) => table[text] ?? text : (text) => text;
