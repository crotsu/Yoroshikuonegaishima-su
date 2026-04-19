#!/bin/bash

INSTALL_DIR="/usr/local/bin"

cp yoroshikuonegaishima-su.py $INSTALL_DIR/yoroshikuonegaishima-su
cp grader.py                  $INSTALL_DIR/grader.py
cp scouter.py                 $INSTALL_DIR/scouter
cp scouterPro.py              $INSTALL_DIR/scouterPro
cp scouterExam.py             $INSTALL_DIR/scouterExam

chmod 755 $INSTALL_DIR/yoroshikuonegaishima-su
chmod 755 $INSTALL_DIR/grader.py
chmod 755 $INSTALL_DIR/scouter
chmod 755 $INSTALL_DIR/scouterPro
chmod 755 $INSTALL_DIR/scouterExam
