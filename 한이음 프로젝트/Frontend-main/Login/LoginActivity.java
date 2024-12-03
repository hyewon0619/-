package com.example.mentos.Login;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.app.AppCompatDelegate;

import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.toolbox.Volley;
import com.example.mentos.Home.HomeActivity;
import com.example.mentos.R;

import org.json.JSONException;
import org.json.JSONObject;

public class LoginActivity extends AppCompatActivity {

//    private EditText emailEditText;
//    private EditText passwordEditText;
//    private Button LoginButton;

    // 알림창 의미
    private AlertDialog dialog;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO);
        setContentView(R.layout.login);  // 액티비티의 레이아웃 설정

        Button SigninButton = findViewById(R.id.btn_sign_in);
        SigninButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent intent = new Intent(LoginActivity.this, SigninActivity.class);
                startActivity(intent);
            }
        });

        final EditText email_text = (EditText) findViewById(R.id.email_text);
        final EditText password_text = (EditText) findViewById(R.id.password_text);
        final Button loginButton = (Button) findViewById(R.id.login_button);


        loginButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent intent = new Intent(LoginActivity.this, HomeActivity.class);
                startActivity(intent);
            }
        });

        
        // 정상적인 로그인 기능
//        loginButton.setOnClickListener(new View.OnClickListener() {
//            @Override
//            public void onClick(View v) {
//                String email = email_text.getText().toString();
//                String password = password_text.getText().toString();
//
//                //
//
//                Response.Listener<JSONObject> responseListener = new Response.Listener<JSONObject>() {
//                    @Override
//                    public void onResponse(JSONObject response) {
//                        
//                        try {
//                            String message = response.getString("message");
//                            if ("User created successfully!".equals(message)) {
//                                runOnUiThread(new Runnable() {
//                                    @Override
//                                    public void run() {
//                                        AlertDialog.Builder builder = new AlertDialog.Builder(LoginActivity.this);
//                                        builder.setMessage("로그인에 성공했습니다.");
////                                                .setNegativeButton("확인", null);
//
//                                        final AlertDialog alertDialog = builder.create();
//                                        alertDialog.show();
//
//                                        // 1초 후에 AlertDialog를 닫는 Handler 추가
//                                        new Handler().postDelayed(new Runnable() {
//                                            @Override
//                                            public void run() {
//                                                if (alertDialog.isShowing()) {
//                                                    alertDialog.dismiss();
//                                                    finish(); // 화면을 종료하고 싶다면 finish() 호출
//                                                }
//                                            }
//                                        }, 600); // 1초(1000ms) 지연
//
//                                        Intent intent =  new Intent(LoginActivity.this, HomeActivity.class);
//                                        LoginActivity.this.startActivity(intent);
//                                        finish();
//                                    }
//                                });
//                            } else {
//                                runOnUiThread(new Runnable() {
//                                    @Override
//                                    public void run() {
//                                        AlertDialog.Builder builder = new AlertDialog.Builder(LoginActivity.this);
//                                        builder.setMessage("계정을 다시 확인하세요.")
//                                                .setNegativeButton("다시 시도", null)
//                                                .show();
//                                    }
//                                });
//                            }
//
//                        }
//                        catch (JSONException e)
//                        {
//                            e.printStackTrace();
//                            // JSON 파싱 에러 로그
//                            Log.e("Register", "JSON parsing error: " + e.getMessage());
//                        }
//                    }
//                };
//
//                try {
//                    LoginRequest loginRequest = new LoginRequest(email, password, responseListener);
//                    RequestQueue queue = Volley.newRequestQueue(LoginActivity.this);
//                    queue.add(loginRequest);
//                } catch (JSONException e) {
//                    e.printStackTrace();
//                }
//            }
//        });
//
    }

    @Override
    protected void onStop() {
        super.onStop();
        if(dialog != null)
        {
            dialog.dismiss();
            dialog = null;
        }
    }


}
