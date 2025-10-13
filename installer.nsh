; 提猫直播助手安装器自定义脚本

; 安装前检查
!macro preInit
  ; 检查是否已安装旧版本
  ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{appId}" "UninstallString"
  StrCmp $R0 "" done
  
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
    "检测到已安装旧版本的提猫直播助手。$\n$\n点击 '确定' 卸载旧版本并继续安装，或点击 '取消' 退出安装。" \
    IDOK uninst
  Abort
  
  uninst:
    ClearErrors
    ExecWait '$R0 _?=$INSTDIR'
    
    IfErrors no_remove_uninstaller done
      Delete $R0
      RMDir $INSTDIR
    no_remove_uninstaller:
  
  done:
!macroend

; 安装完成后的操作
!macro customInstall
  ; 创建防火墙规则（可选）
  ; ExecWait 'netsh advfirewall firewall add rule name="提猫直播助手" dir=in action=allow program="$INSTDIR\${productFilename}" enable=yes'
  
  ; 写入注册表信息
  WriteRegStr HKLM "Software\XingJuAI\TalkingCat" "InstallPath" "$INSTDIR"
  WriteRegStr HKLM "Software\XingJuAI\TalkingCat" "Version" "${version}"
!macroend

; 卸载时的操作
!macro customUnInstall
  ; 删除注册表信息
  DeleteRegKey HKLM "Software\XingJuAI\TalkingCat"
  
  ; 删除防火墙规则（如果之前添加了）
  ; ExecWait 'netsh advfirewall firewall delete rule name="提猫直播助手"'
!macroend