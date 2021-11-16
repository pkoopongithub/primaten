unit UMain;

{$mode objfpc}{$H+}

interface

uses
  Classes, SysUtils, FileUtil, Forms, Controls, Graphics, Dialogs, ExtCtrls,
  Grids, StdCtrls, Unitprimaten;

type
  (* Datentyp fuer die virtuelle Welt*)


  { TfrmMain }

  TfrmMain = class(TForm)
    btnZufall: TButton;
    btnNext: TButton;
    btnStart: TButton;
    btnStopp: TButton;
    Shape1: TShape;
    Shape10: TShape;
    Shape11: TShape;
    Shape12: TShape;
    Shape13: TShape;
    Shape14: TShape;
    Shape15: TShape;
    Shape2: TShape;
    Shape3: TShape;
    Shape4: TShape;
    Shape5: TShape;
    Shape6: TShape;
    Shape7: TShape;
    Shape8: TShape;
    Shape9: TShape;
    Spielfeld: TDrawGrid;
    pnlBottom: TPanel;
    Kulturmonitor: TStringGrid;
    StaticText1: TStaticText;
    StaticText10: TStaticText;
    StaticText11: TStaticText;
    StaticText12: TStaticText;
    StaticText13: TStaticText;
    StaticText14: TStaticText;
    StaticText15: TStaticText;
    StaticText16: TStaticText;
    StaticText2: TStaticText;
    StaticText3: TStaticText;
    StaticText4: TStaticText;
    StaticText5: TStaticText;
    StaticText6: TStaticText;
    StaticText7: TStaticText;
    StaticText8: TStaticText;
    StaticText9: TStaticText;
    tmrAnimation: TTimer;
    procedure Auswerten(Sender: TObject);
    procedure btnStoppClick(Sender: TObject);
    procedure btnStartClick(Sender: TObject);
    procedure btnZufallClick(Sender: TObject);
    procedure FormClose(Sender: TObject; var CloseAction: TCloseAction);
    procedure FormCreate(Sender: TObject);
    procedure KulturmonitorDrawCell(Sender: TObject; aCol, aRow: Integer;
      aRect: TRect; aState: TGridDrawState);
    procedure SpielfeldDrawCell(Sender: TObject; aCol, aRow: Integer;
      aRect: TRect; aState: TGridDrawState);
    procedure StaticText3Click(Sender: TObject);

  private
    { private declarations }

    (* virtuelle Spielwelt *)


  public
    { public declarations }
  end;
PROCEDURE spiel(VAR von,nach :raum);
var
  frmMain: TfrmMain;

implementation

{$R *.lfm}

{ TfrmMain }

procedure TfrmMain.FormCreate(Sender: TObject);
begin
  randomize;
  aufbau;
  FillByte (a,SizeOf(a),0);
  FillByte (b,SizeOf(b),0);
  zufall(a);
  Spielfeld.Repaint;
end;

procedure TfrmMain.KulturmonitorDrawCell(Sender: TObject; aCol, aRow: Integer;
  aRect: TRect; aState: TGridDrawState);
var i:integer;
begin
  i:= a[aCol+1, aRow+1].kultur;

    case i of
        0: Kulturmonitor.Canvas.Brush.Color := clWhite;
        1: Kulturmonitor.Canvas.Brush.Color := clMaroon;
        2: Kulturmonitor.Canvas.Brush.Color := clGreen;
        3: Kulturmonitor.Canvas.Brush.Color := clOlive;
        4: Kulturmonitor.Canvas.Brush.Color := clNavy;
        5: Kulturmonitor.Canvas.Brush.Color := clPurple;
        6: Kulturmonitor.Canvas.Brush.Color := clTeal;
        7: Kulturmonitor.Canvas.Brush.Color := clRed;
        8: Kulturmonitor.Canvas.Brush.Color := clLime;
        9: Kulturmonitor.Canvas.Brush.Color := clYellow;

     end;


 Kulturmonitor.Canvas.FillRect(aRect);
end;



procedure TfrmMain.SpielfeldDrawCell(Sender: TObject; aCol, aRow: Integer;
  aRect: TRect; aState: TGridDrawState);
begin
  if a[aCol+1, aRow+1].status = 1 then
   begin
    if a[aCol+1, aRow+1].geschlecht = 2 then
       Spielfeld.Canvas.Brush.Color := clFuchsia
      else
      if a[aCol+1, aRow+1].geschlecht= 1 then
       Spielfeld.Canvas.Brush.Color := clLime

     end
  else
  begin
    if a[aCol+1, aRow+1].status = 2 then
     begin
      if a[aCol+1, aRow+1].geschlecht = 2 then
       Spielfeld.Canvas.Brush.Color := clRed
      else
      if a[aCol+1, aRow+1].geschlecht = 1 then
       Spielfeld.Canvas.Brush.Color := clGreen

    end
    else
     Spielfeld.Canvas.Brush.Color := clWhite
   end;

 Spielfeld.Canvas.FillRect(aRect);

end;

procedure TfrmMain.StaticText3Click(Sender: TObject);
begin

end;







procedure TfrmMain.Auswerten(Sender: TObject);

begin

    spiel(a,b);
    Spielfeld.Refresh;
    Kulturmonitor.Refresh;
    a:= b;
end;

procedure TfrmMain.btnStoppClick(Sender: TObject);
begin
  tmrAnimation.Enabled := false;
  a:=b;
  Spielfeld.Refresh;
  Kulturmonitor.Refresh;
end;

procedure TfrmMain.btnStartClick(Sender: TObject);
begin
  tmrAnimation.Enabled := true;
end;

procedure TfrmMain.btnZufallClick(Sender: TObject);
begin
  zufall(a);
  Spielfeld.Repaint;
  Kulturmonitor.Repaint;
end;

procedure TfrmMain.FormClose(Sender: TObject; var CloseAction: TCloseAction);
begin
  tmrAnimation.Enabled := false;
  x := xa;
 abbaux(x);
 y := ya;
 abbauy(y);
end;
PROCEDURE spiel(VAR von,nach :raum);
 BEGIN
  y :=ya;
  x :=xa;
  REPEAT
   REPEAT
    nach(.x^.i,y^.i.):=neu(von,x,y);
    frmMain.Kulturmonitor.Cells[x^.i-1,y^.i-1]:=IntToSTR(nach(.x^.i,y^.i.).kultur);
    x := x^.n
   UNTIL x =xa;
   y := y^.n
  UNTIL y =ya;
 END;
end.

