#include "mainwindow.h"
#include "ui_mainwindow.h"

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);
}

MainWindow::~MainWindow()
{
    delete ui;
}
<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>900</width>
    <height>500</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>CX CasparCG Controller - 2.28.2016 </string>
  </property>
  <widget class="QWidget" name="centralWidget">
   <widget class="QWidget" name="gridLayoutWidget_2">
    <property name="geometry">
     <rect>
      <x>-1</x>
      <y>-1</y>
      <width>901</width>
      <height>461</height>
     </rect>
    </property>
    <layout class="QGridLayout" name="gridLayout_2">
     <property name="leftMargin">
      <number>10</number>
     </property>
     <property name="topMargin">
      <number>10</number>
     </property>
     <property name="rightMargin">
      <number>10</number>
     </property>
     <property name="bottomMargin">
      <number>10</number>
     </property>
     <item row="1" column="0">
      <widget class="QGroupBox" name="commentators_groupBox">
       <property name="title">
        <string>Commentators (1-10)</string>
       </property>
       <widget class="QWidget" name="gridLayoutWidget_3">
        <property name="geometry">
         <rect>
          <x>0</x>
          <y>10</y>
          <width>191</width>
          <height>141</height>
         </rect>
        </property>
        <layout class="QGridLayout" name="gridLayout">
         <property name="leftMargin">
          <number>10</number>
         </property>
         <property name="topMargin">
          <number>10</number>
         </property>
         <property name="rightMargin">
          <number>10</number>
         </property>
         <property name="bottomMargin">
          <number>10</number>
         </property>
         <property name="spacing">
          <number>6</number>
         </property>
         <item row="1" column="0">
          <widget class="QLabel" name="label_2">
           <property name="text">
            <string>Left: </string>
           </property>
           <property name="alignment">
            <set>Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter</set>
           </property>
          </widget>
         </item>
         <item row="2" column="0">
          <widget class="QLabel" name="label_3">
           <property name="text">
            <string>Right: </string>
           </property>
           <property name="alignment">
            <set>Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter</set>
           </property>
          </widget>
         </item>
         <item row="0" column="0">
          <widget class="QLabel" name="label">
           <property name="text">
            <string>Title: </string>
           </property>
           <property name="alignment">
            <set>Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter</set>
           </property>
          </widget>
         </item>
         <item row="0" column="1">
          <widget class="QLineEdit" name="commentator_title">
           <property name="font">
            <font>
             <pointsize>10</pointsize>
            </font>
           </property>
          </widget>
         </item>
         <item row="1" column="1">
          <widget class="QLineEdit" name="commentator_left">
           <property name="font">
            <font>
             <pointsize>10</pointsize>
            </font>
           </property>
          </widget>
         </item>
         <item row="2" column="1">
          <widget class="QLineEdit" name="commentator_right">
           <property name="font">
            <font>
             <pointsize>10</pointsize>
            </font>
           </property>
          </widget>
         </item>
         <item row="3" column="0" colspan="2">
          <layout class="QHBoxLayout" name="buttonBox">
           <item>
            <widget class="QPushButton" name="commentator_play">
             <property name="text">
              <string>PLAY</string>
             </property>
            </widget>
           </item>
           <item>
            <widget class="QPushButton" name="commentator_stop">
             <property name="text">
              <string>STOP</string>
             </property>
            </widget>
           </item>
           <item>
            <widget class="QPushButton" name="pushButton">
             <property name="text">
              <string>UPDATE</string>
             </property>
             <property name="iconSize">
              <size>
               <width>16</width>
               <height>16</height>
              </size>
             </property>
            </widget>
           </item>
          </layout>
         </item>
        </layout>
       </widget>
      </widget>
     </item>
     <item row="0" column="0">
      <layout class="QGridLayout" name="grid_top"/>
     </item>
    </layout>
   </widget>
  </widget>
  <widget class="QMenuBar" name="menuBar">
   <property name="geometry">
    <rect>
     <x>0</x>
     <y>0</y>
     <width>900</width>
     <height>21</height>
    </rect>
   </property>
   <widget class="QMenu" name="menuHello">
    <property name="title">
     <string>File</string>
    </property>
    <addaction name="actionExit"/>
   </widget>
   <addaction name="menuHello"/>
  </widget>
  <widget class="QStatusBar" name="statusBar"/>
  <action name="actionExit">
   <property name="text">
    <string>Exit...</string>
   </property>
  </action>
 </widget>
 <layoutdefault spacing="6" margin="11"/>
 <resources/>
 <connections/>
</ui>
