# -*- mode: python -*-

block_cipher = None

added_files = [('.\\LOGIN\\login.json','./LOGIN'),
				('.\\LOGIN\\knownFacesEncodings.npy','./LOGIN'),
				('.\\LOGIN\\knownFacesNames.txt','./LOGIN'),
				('.\\LOGIN\\nameVSid.txt','./LOGIN')
]

face_models = [
('.\\face_recognition_models\\models\\dlib_face_recognition_resnet_model_v1.dat', './face_recognition_models/models'),
('.\\face_recognition_models\\models\\mmod_human_face_detector.dat', './face_recognition_models/models'),
('.\\face_recognition_models\\models\\shape_predictor_5_face_landmarks.dat', './face_recognition_models/models'),
('.\\face_recognition_models\\models\\shape_predictor_68_face_landmarks.dat', './face_recognition_models/models'),
]

a = Analysis(['face recognition.py'],
             pathex=['C:\\Users\\astrea\\Desktop\\PythonSalesforce\\OMO DE'],
             binaries=face_models,
             datas=added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
			 
			 
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='face recognition',
          debug=True,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
